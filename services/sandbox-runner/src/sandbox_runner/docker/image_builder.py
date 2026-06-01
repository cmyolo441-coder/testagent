"""Image Builder — Build Docker images for sandbox environments"""
import subprocess
import json
import tempfile
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BuildResult:
    success: bool
    image_tag: str
    image_id: str
    build_output: str
    duration_ms: float
    size_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "image_tag": self.image_tag,
            "image_id": self.image_id,
            "build_output": self.build_output[:2000],
            "duration_ms": self.duration_ms,
            "size_bytes": self.size_bytes,
        }


class ImageBuilder:
    """Build Docker images for sandboxed execution."""

    BASE_DOCKERFILE = """\
FROM {base_image}
RUN apt-get update && apt-get install -y --no-install-recommends \\
    {packages} \\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
USER nobody
"""

    PYTHON_DOCKERFILE = """\
FROM python:3.12-slim
RUN pip install --no-cache-dir {packages}
WORKDIR /workspace
USER nobody
"""

    NODE_DOCKERFILE = """\
FROM node:20-slim
RUN npm install -g {packages}
WORKDIR /workspace
USER node
"""

    def __init__(self, docker_bin: str = "docker"):
        self.docker_bin = docker_bin
        self._built_images: list[dict] = []

    def build(self, dockerfile_content: str = None, tag: str = None,
              base_image: str = "python:3.12-slim",
              packages: list[str] = None,
              dockerfile_path: str = None,
              build_args: dict = None) -> BuildResult:
        import time
        start = time.time()

        if tag is None:
            tag = f"sandbox-{base_image.split(':')[0]}:local"

        if dockerfile_content is None:
            dockerfile_content = self._generate_dockerfile(
                base_image, packages or []
            )

        tmpdir = tempfile.mkdtemp(prefix="sandbox-build-")
        dockerfile_loc = os.path.join(tmpdir, "Dockerfile")

        with open(dockerfile_loc, "w") as f:
            f.write(dockerfile_content)

        docker_cmd = [self.docker_bin, "build", "-t", tag, "-f", dockerfile_loc]

        if build_args:
            for k, v in build_args.items():
                docker_cmd.extend(["--build-arg", f"{k}={v}"])

        docker_cmd.append(tmpdir)

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            duration = (time.time() - start) * 1000

            image_id = self._get_image_id(tag)
            size_bytes = self._get_image_size(tag)

            success = result.returncode == 0

            if success:
                self._built_images.append({
                    "tag": tag,
                    "image_id": image_id,
                    "size_bytes": size_bytes,
                })

            return BuildResult(
                success=success,
                image_tag=tag,
                image_id=image_id,
                build_output=result.stdout + result.stderr,
                duration_ms=duration,
                size_bytes=size_bytes,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return BuildResult(
                success=False,
                image_tag=tag,
                image_id="",
                build_output=str(e),
                duration_ms=duration,
            )
        finally:
            try:
                os.remove(dockerfile_loc)
                os.rmdir(tmpdir)
            except Exception:
                pass

    def build_sandbox_image(self, language: str, packages: list[str] = None,
                            extra_files: dict[str, str] = None) -> BuildResult:
        packages = packages or []

        if language == "python":
            dockerfile = self.PYTHON_DOCKERFILE.format(packages=" ".join(packages))
            tag = f"sandbox-python:local"
            base = "python:3.12-slim"
        elif language == "node" or language == "javascript":
            dockerfile = self.NODE_DOCKERFILE.format(packages=" ".join(packages))
            tag = f"sandbox-node:local"
            base = "node:20-slim"
        else:
            dockerfile = self.BASE_DOCKERFILE.format(
                base_image=base,
                packages=" ".join(packages),
            )
            tag = f"sandbox-{language}:local"
            base = f"{language}:latest"

        return self.build(
            dockerfile_content=dockerfile,
            tag=tag,
            base_image=base,
            packages=packages,
        )

    def list_images(self, pattern: str = "sandbox") -> list[dict]:
        try:
            result = subprocess.run(
                [self.docker_bin, "images", "--format", "json", pattern],
                capture_output=True,
                text=True,
                timeout=10,
            )
            images = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    images.append(json.loads(line))
            return images
        except Exception:
            return []

    def remove_image(self, tag: str) -> bool:
        try:
            result = subprocess.run(
                [self.docker_bin, "rmi", "-f", tag],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _generate_dockerfile(self, base_image: str, packages: list[str]) -> str:
        pkg_str = " ".join(packages) if packages else "curl wget"
        return self.BASE_DOCKERFILE.format(
            base_image=base_image,
            packages=pkg_str,
        )

    def _get_image_id(self, tag: str) -> str:
        try:
            result = subprocess.run(
                [self.docker_bin, "inspect", "--format", "{{.Id}}", tag],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip()[:19] if result.returncode == 0 else ""
        except Exception:
            return ""

    def _get_image_size(self, tag: str) -> int:
        try:
            result = subprocess.run(
                [self.docker_bin, "inspect", "--format", "{{.Size}}", tag],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return int(result.stdout.strip()) if result.returncode == 0 else 0
        except Exception:
            return 0
