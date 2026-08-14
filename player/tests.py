from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from music.models import Song
from music.tests import TEST_MEDIA, make_wav_bytes

from .models import Favorite, ListeningHistory


@TEST_MEDIA
class PlayerApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("bob", password="pw-secret-123")
        self.song = Song.objects.create(
            title="Test",
            owner=self.user,
            audio_file=SimpleUploadedFile("t.wav", make_wav_bytes()),
        )
        self.client.force_login(self.user)

    def test_toggle_favorite_on_and_off(self):
        url = reverse("player:toggle_favorite", args=[self.song.pk])
        r1 = self.client.post(url)
        self.assertTrue(r1.json()["isFavorite"])
        self.assertEqual(Favorite.objects.count(), 1)

        r2 = self.client.post(url)
        self.assertFalse(r2.json()["isFavorite"])
        self.assertEqual(Favorite.objects.count(), 0)

    def test_record_play_stores_position(self):
        url = reverse("player:record_play", args=[self.song.pk])
        self.client.post(url, data={"position": 42}, content_type="application/json")
        history = ListeningHistory.objects.get(user=self.user, song=self.song)
        self.assertEqual(history.playback_position, 42)

    def test_cannot_favorite_another_users_song(self):
        other = User.objects.create_user("eve", password="pw-secret-123")
        other_song = Song.objects.create(
            title="Private",
            owner=other,
            audio_file=SimpleUploadedFile("p.wav", make_wav_bytes()),
        )
        url = reverse("player:toggle_favorite", args=[other_song.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
