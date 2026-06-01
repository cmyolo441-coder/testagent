"""Email Tools — Email sending and reading operations"""
import subprocess
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class EmailResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    operation: str = ""
    message_id: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "operation": self.operation,
            "message_id": self.message_id,
            "duration_ms": self.duration_ms,
        }


@dataclass
class EmailMessage:
    from_addr: str = ""
    to_addrs: list[str] = field(default_factory=list)
    cc_addrs: list[str] = field(default_factory=list)
    bcc_addrs: list[str] = field(default_factory=list)
    subject: str = ""
    body: str = ""
    html_body: str = ""
    attachments: list[str] = field(default_factory=list)
    reply_to: str = ""
    priority: str = "normal"  # low, normal, high


class EmailTools:
    """Email sending and reading operations."""

    MAX_ATTACHMENT_SIZE_MB = 10
    MAX_SUBJECT_LENGTH = 998
    MAX_BODY_LENGTH = 1000000

    def __init__(self, smtp_host: str = "", smtp_port: int = 587,
                 smtp_user: str = "", smtp_password: str = "",
                 use_tls: bool = True):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self._sent_messages: list[dict] = []

    def send(self, message: EmailMessage) -> EmailResult:
        start = time.time()

        if not message.from_addr:
            return EmailResult(
                success=False,
                error="Sender address is required",
                operation="send",
            )

        if not message.to_addrs:
            return EmailResult(
                success=False,
                error="At least one recipient is required",
                operation="send",
            )

        if not self.smtp_host:
            return EmailResult(
                success=False,
                error="SMTP host not configured",
                operation="send",
            )

        validation_error = self._validate_message(message)
        if validation_error:
            return EmailResult(
                success=False,
                error=validation_error,
                operation="send",
            )

        try:
            msg = MIMEMultipart()
            msg["From"] = message.from_addr
            msg["To"] = ", ".join(message.to_addrs)
            if message.cc_addrs:
                msg["Cc"] = ", ".join(message.cc_addrs)
            msg["Subject"] = message.subject
            msg["Reply-To"] = message.reply_to or message.from_addr

            if message.priority == "high":
                msg["X-Priority"] = "1"
            elif message.priority == "low":
                msg["X-Priority"] = "5"

            if message.html_body:
                msg.attach(MIMEText(message.html_body, "html"))
            else:
                msg.attach(MIMEText(message.body, "plain"))

            for attachment_path in message.attachments:
                attach_result = self._attach_file(msg, attachment_path)
                if not attach_result["success"]:
                    return EmailResult(
                        success=False,
                        error=attach_result["error"],
                        operation="send",
                        duration_ms=(time.time() - start) * 1000,
                    )

            all_recipients = message.to_addrs + message.cc_addrs + message.bcc_addrs

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(message.from_addr, all_recipients, msg.as_string())

            duration = (time.time() - start) * 1000
            message_id = msg.get("Message-ID", f"msg-{int(time.time())}")

            sent_record = {
                "message_id": message_id,
                "from": message.from_addr,
                "to": message.to_addrs,
                "subject": message.subject,
                "timestamp": time.time(),
            }
            self._sent_messages.append(sent_record)

            return EmailResult(
                success=True,
                data=sent_record,
                operation="send",
                message_id=message_id,
                duration_ms=duration,
            )

        except smtplib.SMTPAuthenticationError:
            return EmailResult(
                success=False,
                error="SMTP authentication failed",
                operation="send",
                duration_ms=(time.time() - start) * 1000,
            )
        except smtplib.SMTPException as e:
            return EmailResult(
                success=False,
                error=f"SMTP error: {str(e)}",
                operation="send",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return EmailResult(
                success=False,
                error=str(e),
                operation="send",
                duration_ms=(time.time() - start) * 1000,
            )

    def send_simple(self, to: str, subject: str, body: str,
                    from_addr: str = "") -> EmailResult:
        message = EmailMessage(
            from_addr=from_addr or self.smtp_user,
            to_addrs=[to] if isinstance(to, str) else to,
            subject=subject,
            body=body,
        )
        return self.send(message)

    def read_local(self, mailbox_path: str, limit: int = 10) -> EmailResult:
        start = time.time()
        try:
            path = Path(mailbox_path)
            if not path.exists():
                return EmailResult(
                    success=False,
                    error=f"Mailbox not found: {mailbox_path}",
                    operation="read",
                )

            content = path.read_text(errors="ignore")
            lines = content.split("\n")

            messages = []
            current_msg = {}
            for line in lines:
                if line.startswith("From:"):
                    if current_msg:
                        messages.append(current_msg)
                    current_msg = {"from": line[5:].strip()}
                elif line.startswith("To:"):
                    current_msg["to"] = line[4:].strip()
                elif line.startswith("Subject:"):
                    current_msg["subject"] = line[9:].strip()
                elif line.startswith("Date:"):
                    current_msg["date"] = line[6:].strip()
                elif line.startswith("Body:") or line.startswith("Content:"):
                    current_msg["body"] = line.split(":", 1)[1].strip()

            if current_msg:
                messages.append(current_msg)

            duration = (time.time() - start) * 1000
            return EmailResult(
                success=True,
                data={"messages": messages[-limit:], "count": len(messages)},
                operation="read",
                duration_ms=duration,
            )
        except Exception as e:
            return EmailResult(
                success=False,
                error=str(e),
                operation="read",
                duration_ms=(time.time() - start) * 1000,
            )

    def get_sent_messages(self) -> list[dict]:
        return list(self._sent_messages)

    def _validate_message(self, message: EmailMessage) -> str:
        if len(message.subject) > self.MAX_SUBJECT_LENGTH:
            return f"Subject too long ({len(message.subject)} > {self.MAX_SUBJECT_LENGTH})"
        if len(message.body) > self.MAX_BODY_LENGTH:
            return f"Body too long ({len(message.body)} > {self.MAX_BODY_LENGTH})"
        for addr in message.to_addrs + message.cc_addrs:
            if "@" not in addr:
                return f"Invalid email address: {addr}"
        for attachment in message.attachments:
            path = Path(attachment)
            if not path.exists():
                return f"Attachment not found: {attachment}"
            if path.stat().st_size > self.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024:
                return f"Attachment too large: {attachment}"
        return ""

    def _attach_file(self, msg: MIMEMultipart, filepath: str) -> dict:
        try:
            path = Path(filepath)
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={path.name}")
            msg.attach(part)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
