"""Jailer — Apply resource and security constraints to Firecracker microVMs"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JailConfig:
    uid: int = 65534
    gid: int = 65534
    cpu_list: str = ""
    memory_limit_mib: int = 256
    network_interfaces: list[str] = field(default_factory=list)
    chroot_base: str = "/srv/jailer"
    daemonize: bool = True
    seccomp_filter: Optional[str] = None
    cap_drop: list[str] = field(default_factory=lambda: ["ALL"])
    readonly_paths: list[str] = field(default_factory=list)
    tmpfs_mounts: list[str] = field(default_factory=list)

    def to_jailer_args(self) -> list[str]:
        args = [
            "--id", f"jail-{int(os.getpid())}",
            "--uid", str(self.uid),
            "--gid", str(self.gid),
            "--chroot-base-dir", self.chroot_base,
        ]
        if self.cpu_list:
            args.extend(["--cpu-list", self.cpu_list])
        if self.daemonize:
            args.append("--daemonize")
        if self.seccomp_filter:
            args.extend(["--seccomp-filter", self.seccomp_filter])
        return args

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "gid": self.gid,
            "cpu_list": self.cpu_list,
            "memory_limit_mib": self.memory_limit_mib,
            "chroot_base": self.chroot_base,
            "daemonize": self.daemonize,
            "seccomp_filter": self.seccomp_filter,
        }


class Jailer:
    """Apply resource and security constraints to Firecracker microVMs."""

    DEFAULT_CHROOT = "/srv/jailer"

    SECCOMP_BASIC_FILTER = {
        "default_action": "SCMP_ACT_ERRNO",
        "architectures": ["SCMP_ARCH_X86_64"],
        "syscalls": [
            {"names": ["read", "write", "open", "close", "stat", "fstat",
                       "lstat", "poll", "lseek", "mmap", "mprotect", "munmap",
                       "brk", "ioctl", "access", "pipe", "select", "sched_yield",
                       "mremap", "msync", "mincore", "madvise", "dup", "dup2",
                       "nanosleep", "getpid", "clone", "fork", "vfork",
                       "execve", "exit", "wait4", "kill", "uname",
                       "fcntl", "flock", "fsync", "fdatasync", "truncate",
                       "ftruncate", "getdents", "getcwd", "chdir",
                       "rename", "mkdir", "rmdir", "link", "unlink",
                       "chmod", "chown", "umask", "gettimeofday",
                       "getuid", "getgid", "geteuid", "getegid",
                       "getppid", "getpgrp", "setsid", "setreuid",
                       "setregid", "getgroups", "setgroups",
                       "sigaltstack", "rt_sigaction", "rt_sigprocmask",
                       "rt_sigreturn", "socket", "connect", "accept",
                       "sendto", "recvfrom", "sendmsg", "recvmsg",
                       "shutdown", "bind", "listen", "getsockname",
                       "getpeername", "socketpair", "setsockopt",
                       "getsockopt", "clone", "fork",
                       "vfork", "execve", "exit", "exit_group",
                       "wait4", "waitid", "kill", "uname",
                       "semget", "semctl", "semop", "shmdt",
                       "shmget", "shmctl", "msgget", "msgctl",
                       "msgrcv", "msgsnd", "fcntl", "flock",
                       "fsync", "fdatasync", "ftruncate",
                       "getdents", "getcwd", "chdir", "fchdir",
                       "rename", "mkdir", "rmdir", "link",
                       "unlink", "symlink", "readlink",
                       "chmod", "fchmod", "chown", "fchown",
                       "lchown", "umask", "gettimeofday",
                       "getrlimit", "getrusage", "sysinfo",
                       "times", "ptrace", "syslog", "getuid",
                       "getgid", "setuid", "setgid", "geteuid",
                       "getegid", "setpgid", "getppid", "getpgrp",
                       "setsid", "setreuid", "setregid",
                       "getgroups", "setgroups", "setresuid",
                       "getresuid", "setresgid", "getresgid",
                       "getpgid", "setfsuid", "setfsgid",
                       "getsid", "capget", "capset",
                       "rt_sigpending", "rt_sigtimedwait",
                       "rt_sigqueueinfo", "rt_sigsuspend",
                       "sigaltstack", "utime", "mount",
                       "pivot_root", "chroot", "sync",
                       "acct", "umount2", "swapon",
                       "swapoff", "reboot", "sethostname",
                       "setdomainname", "iopl", "ioperm",
                       "create_module", "init_module",
                       "delete_module", "get_kernel_syms",
                       "query_module", "quotactl",
                       "nfsservctl", "sysfs", "sysinfo",
                       "ustat", "personality", "afs_syscall",
                       "ptrace", "mount", "umount2",
                       "ptrace", "alarm", "getitimer",
                       "setitimer", "kexec_load", "init_module",
                       "delete_module", "timer_create",
                       "timer_gettime", "timer_getoverrun",
                       "timer_settime", "timer_delete",
                       "clock_settime", "clock_gettime",
                       "clock_getres", "clock_nanosleep",
                       "exit_group", "epoll_wait", "epoll_ctl",
                       "tgkill", "utimes", "vserver",
                       "mbind", "set_mempolicy",
                       "get_mempolicy", "mq_open",
                       "mq_unlink", "mq_timedsend",
                       "mq_timedreceive", "mq_notify",
                       "mq_getsetattr", "kexec_file_load",
                       "waitid", "add_key", "request_key",
                       "keyctl", "ioprio_set", "ioprio_get",
                       "inotify_init", "inotify_add_watch",
                       "inotify_rm_watch", "migrate_pages",
                       "openat", "mkdirat", "mknodat",
                       "fchownat", "futimesat", "newfstatat",
                       "unlinkat", "renameat", "linkat",
                       "symlinkat", "readlinkat", "fchmodat",
                       "faccessat", "pselect6", "ppoll",
                       "unshare", "set_robust_list",
                       "get_robust_list", "splice",
                       "tee", "sync_file_range",
                       "utimensat", "epoll_pwait",
                       "signalfd", "timerfd_create",
                       "eventfd", "fallocate", "timerfd_settime",
                       "timerfd_gettime", "accept4",
                       "signalfd4", "eventfd2", "epoll_create1",
                       "dup3", "pipe2", "inotify_init1",
                       "preadv", "pwritev", "rt_tgsigqueueinfo",
                       "perf_event_open", "recvmmsg",
                       "fanotify_init", "fanotify_mark",
                       "prlimit64", "name_to_handle_at",
                       "open_by_handle_at", "clock_adjtime",
                       "syncfs", "sendmmsg", "setns",
                       "getcpu", "process_vm_readv",
                       "process_vm_writev", "kcmp",
                       "finit_module", "sched_setattr",
                       "sched_getattr", "renameat2",
                       "seccomp", "getrandom", "memfd_create",
                       "kexec_file_load", "bpf",
                       "execveat", "userfaultfd",
                       "membarrier", "mlock2",
                       "copy_file_range", "preadv2",
                       "pwritev2", "pkey_mprotect",
                       "pkey_alloc", "pkey_free",
                       "statx", "io_pgetevents",
                       "rseq", "uretprobe"],
             "action": "SCMP_ACT_ALLOW"},
        ],
    }

    def __init__(self):
        self.active_jails: dict[str, JailConfig] = {}

    def configure(self, uid: int = 65534, gid: int = 65534,
                  cpu_list: str = "", memory_limit_mib: int = 256,
                  daemonize: bool = True) -> JailConfig:
        config = JailConfig(
            uid=uid,
            gid=gid,
            cpu_list=cpu_list,
            memory_limit_mib=memory_limit_mib,
            daemonize=daemonize,
            chroot_base=self.DEFAULT_CHROOT,
        )

        jail_id = f"jail-{uid}-{int(memory_limit_mib)}"
        self.active_jails[jail_id] = config

        return config

    def configure_restricted(self) -> JailConfig:
        return self.configure(
            uid=65534,
            gid=65534,
            cpu_list="0",
            memory_limit_mib=128,
            daemonize=True,
        )

    def configure_network_isolated(self) -> JailConfig:
        config = self.configure()
        config.network_interfaces = []
        return config

    def get_jailer_command(self, firecracker_bin: str, config: JailConfig) -> list[str]:
        cmd = [self._find_jailer()]
        cmd.extend(config.to_jailer_args())
        cmd.append(firecracker_bin)
        return cmd

    def _find_jailer(self) -> str:
        for path in ["/usr/local/bin/jailer", "/opt/firecracker/jailer", "jailer"]:
            if os.path.exists(path):
                return path
        return "jailer"

    def get_active_jails(self) -> dict[str, JailConfig]:
        return dict(self.active_jails)

    def remove_jail(self, jail_id: str) -> bool:
        if jail_id in self.active_jails:
            del self.active_jails[jail_id]
            return True
        return False
