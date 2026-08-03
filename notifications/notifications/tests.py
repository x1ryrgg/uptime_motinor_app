from django.test import TestCase
from .services import EmailSender, TgSender

def test_main():
    sender = EmailSender()
    sender.send(title='test', message='message test', target='zhdamarovd@inbox.ru')


if __name__ == "__main__":
    test_main()
