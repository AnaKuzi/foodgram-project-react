from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        'E-mail',
        unique=True,
        blank=False,
        max_length=254,
        error_messages={'unique': 'Этот e-mail уже зарегестрирован.'},
    )
    first_name = models.CharField('Имя пользователя',
                                  max_length=150,
                                  blank=False)
    last_name = models.CharField('Фамилия пользователя',
                                 max_length=150,
                                 blank=False)

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_and_email'
            )
        ]
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'pk: {self.id} email={self.email}'


class Follow(models.Model):
    """Модель подписок."""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='follower')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="following",
                               verbose_name="following")

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_following',
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user_id} подписан на {self.author_id}'
