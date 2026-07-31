import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from monitors.models import Monitor, CheckResult, HTTPMethod



class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми мониторами и историей проверок"

    def add_arguments(self, parser):
        parser.add_argument(
            "--checks-count",
            type=int,
            default=50,
            help="Количество исторической информации для каждого монитора (по умолчанию: 50)",
        )

    def handle(self, *args, **options):
        checks_count = options["checks_count"]

        self.stdout.write(self.style.WARNING("Начинаем генерацию тестовых данных..."))

        user = 1 # поменять

        self.stdout.write(
            self.style.SUCCESS(
                "Используется существующий пользователь: root@example.com"
            )
        )

        # 2. Набор тестовых сайтов
        test_services = [
            {
                "name": "Google Search",
                "url": "https://www.google.com",
                "method": HTTPMethod.GET,
                "interval_seconds": 30,
                "expected_status_code": 200,
                "expected_keyword": "Google",
                "is_active": True,
                "is_currently_up": True,
            },
            {
                "name": "GitHub API",
                "url": "https://api.github.com",
                "method": HTTPMethod.GET,
                "interval_seconds": 60,
                "expected_status_code": 200,
                "expected_keyword": "current_user_url",
                "is_active": True,
                "is_currently_up": True,
            },
            {
                "name": "Python Official",
                "url": "https://www.python.org",
                "method": HTTPMethod.GET,
                "interval_seconds": 120,
                "expected_status_code": 200,
                "expected_keyword": "Python",
                "is_active": True,
                "is_currently_up": True,
            },
            {
                "name": "Failing Service Test",
                "url": "https://httpbin.org/status/500",
                "method": HTTPMethod.GET,
                "interval_seconds": 60,
                "expected_status_code": 200,
                "expected_keyword": "",
                "is_active": True,
                "is_currently_up": False,
            },
            {
                "name": "Broken URL (Timeout Test)",
                "url": "https://nonexistent-domain-test-123456.org",
                "method": HTTPMethod.GET,
                "interval_seconds": 300,
                "expected_status_code": 200,
                "expected_keyword": "",
                "is_active": False,
                "is_currently_up": False,
            },
        ]

        now = timezone.now()

        for data in test_services:
            monitor, m_created = Monitor.objects.get_or_create(
                user=user,
                url=data["url"],
                defaults=data,
            )

            status_text = "создан" if m_created else "уже существует"
            self.stdout.write(f"Монитор '{monitor.name}' ({status_text})")

            # 3. Генерируем историю проверок
            check_results_to_create = []

            # Генерируем даты проверок от прошлого к настоящему
            for i in range(checks_count, 0, -1):
                checked_time = now - timedelta(minutes=i * 5)

                if monitor.is_currently_up:
                    # Редкий случай случайной ошибки (5% шанса)
                    is_success = random.random() > 0.05
                    status_code = 200 if is_success else random.choice([500, 502, 503])
                    response_time = (
                        random.randint(40, 250)
                        if is_success
                        else random.randint(800, 2500)
                    )
                    error_msg = (
                        None if is_success else f"Сервер вернул ошибку {status_code}"
                    )
                else:
                    is_success = False
                    status_code = 500 if "httpbin" in monitor.url else None
                    response_time = random.randint(1500, 3000)
                    error_msg = (
                        "Ожидался статус 200, получен 500"
                        if status_code == 500
                        else "Ошибка сети: Name or service not known"
                    )

                check_results_to_create.append(
                    CheckResult(
                        monitor=monitor,
                        checked_at=checked_time,
                        status_code=status_code,
                        response_time_ms=response_time,
                        is_success=is_success,
                        error_message=error_msg,
                    )
                )

            #
            CheckResult.objects.bulk_create(check_results_to_create)
            self.stdout.write(f" Добавлено {checks_count} записей проверок в историю.")

        self.stdout.write(
            self.style.SUCCESS("🎉 Заполнение тестовыми данными успешно завершено!")
        )
