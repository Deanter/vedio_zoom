from __future__ import annotations

from urllib.parse import urlparse

from .models import Platform


class InvalidUrlError(ValueError):
    """URL не соответствует требованиям сервиса."""


_PLATFORM_HOSTS = {
    Platform.YOUTUBE: {"youtube.com", "www.youtube.com", "youtu.be"},
    Platform.TIKTOK: {"tiktok.com", "www.tiktok.com", "vm.tiktok.com"},
    Platform.INSTAGRAM: {"instagram.com", "www.instagram.com"},
}


def detect_platform(url: str) -> Platform:
    """Определяет платформу по URL и валидирует схему/хост."""
    parsed = urlparse(url)

    if not parsed.scheme or parsed.scheme.lower() != "https":
        raise InvalidUrlError("Only HTTPS links are supported.")

    host = parsed.netloc.lower()
    if not host:
        raise InvalidUrlError("URL host is missing.")

    for platform, hosts in _PLATFORM_HOSTS.items():
        if host in hosts:
            return platform

    raise InvalidUrlError("Unsupported video host.")

