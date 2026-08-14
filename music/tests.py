import io
import struct
import tempfile
import wave

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

# Keep test uploads out of the real media/ directory.
TEST_MEDIA = override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pocketbeats-test-"))

from .schemas import SongMetadata
from .validators import read_audio_duration, validate_audio_file


def make_wav_bytes(seconds=1, rate=8000):
    buf = io.BytesIO()
    with wave.open(buf, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", 0) for _ in range(seconds * rate)))
    return buf.getvalue()


class SongMetadataSchemaTests(TestCase):
    def test_strips_and_validates(self):
        meta = SongMetadata(title="  Hello  ", artist=" World ")
        self.assertEqual(meta.title, "Hello")
        self.assertEqual(meta.artist, "World")

    def test_rejects_empty_title(self):
        with self.assertRaises(Exception):
            SongMetadata(title="   ")

    def test_rejects_impossible_year(self):
        with self.assertRaises(Exception):
            SongMetadata(title="Song", release_year=1200)


class AudioValidatorTests(TestCase):
    def test_accepts_real_wav(self):
        upload = SimpleUploadedFile(
            "song.wav", make_wav_bytes(), content_type="audio/wav"
        )
        validate_audio_file(upload)  # should not raise

    def test_rejects_fake_audio(self):
        upload = SimpleUploadedFile(
            "fake.mp3", b"this is not audio", content_type="audio/mpeg"
        )
        with self.assertRaises(ValidationError):
            validate_audio_file(upload)

    def test_reads_duration(self):
        upload = SimpleUploadedFile("song.wav", make_wav_bytes(seconds=2))
        self.assertEqual(read_audio_duration(upload), 2)


@TEST_MEDIA
class LibraryViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pw-secret-123")

    def test_library_requires_login(self):
        response = self.client.get(reverse("music:library"))
        self.assertEqual(response.status_code, 302)

    def test_upload_flow_creates_song(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            "track.wav", make_wav_bytes(seconds=1), content_type="audio/wav"
        )
        response = self.client.post(
            reverse("music:upload"),
            {"title": "My Song", "artist": "Me", "audio_file": upload,
             "agree_rights": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.songs.count(), 1)
        self.assertEqual(self.user.songs.first().title, "My Song")
