from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['config/settings.toml'],
    environments=True,
    load_dotenv=True,
    envvar_prefix="MYAPP",
)


# Эта функция позволяет динамически изменять настройки
def update_settings(key, value):
    settings.set(key, value)
