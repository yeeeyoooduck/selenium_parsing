import time
from selenium import webdriver
from selenium.webdriver.common.by import By


def open_in_browser(func):
    """
    Декоратор, который открывает веб-браузер, выполняет функцию, а затем закрывает браузер.
    Обертывает другие функции для автоматизации процесса открытия и закрытия браузера.

    :param func: Принимаем функцию, которую нужно обернуть.
    :return: Возвращаем обернутую функцию.
    """

    def _wrapper(link, *args, **kwargs):
        driver = webdriver.Firefox()
        try:
            driver.get(link)
            time.sleep(8)
            result = func(driver, *args, **kwargs)
        except Exception as error:
            print(f"Ошибка! {error}")
            return func
        else:
            return result
        finally:
            driver.close()
            driver.quit()

    return _wrapper


@open_in_browser
def get_greenspark_prices_and_quantity(driver):
    """
    Получить розничную и оптовую цену с url GreenSpark используя декоратор с библиотекой 'selenium'.

    :return: Возвращает словарь с розничной и оптовой ценой.
    """
    prices_and_quantity = {}

    try:
        prices_elements = driver.find_elements(By.CLASS_NAME, 'price')
        for element in prices_elements:
            parent_element = element.find_element(By.XPATH, '..')
            parent_splitted_elements = parent_element.text.split('\n')
            if parent_splitted_elements[0] == "Столичный":
                prices_and_quantity['Розничная цена'] = parent_splitted_elements[1]
            elif parent_splitted_elements[0] == "Столичный (опт)":
                prices_and_quantity['Оптовая цена'] = parent_splitted_elements[1]

        quantity_elements = driver.find_elements(By.CLASS_NAME, 'quantity')
        quantity_specificators = ['осталось мало', 'осталось немного', 'есть в наличии', 'нет в наличии']
        for element in quantity_elements:
            for sub_element in element.text.split('\n'):
                if sub_element in quantity_specificators:
                    prices_and_quantity['Наличие'] = sub_element
    except:
        pass
    finally:
        return prices_and_quantity


@open_in_browser
def get_mobchasti_prices_and_quantity(driver):
    """
    Получить розничную и оптовую цену с url MobChasti используя декоратор с библиотекой 'selenium'.

    :return: Возвращает словарь с розничной и оптовой ценой.
    """
    prices_and_quantity = {}

    try:
        prices_elements = driver.find_elements(By.CLASS_NAME, 'price')
        for element in prices_elements:
            for sub_element in element.text.split('\n'):
                if sub_element.replace('руб.', '').replace(' ', '').isdigit():
                    prices_and_quantity['Розничная цена'] = int(sub_element.replace('руб.', '').replace(' ', ''))

        quantity_elements = driver.find_elements(By.CLASS_NAME, 'sklad')
        for element in quantity_elements:
            if element.text.split('\n')[0] == 'г. Подольск':
                prices_and_quantity['Наличие'] = element.text.split('\n')[1]
    except Exception:
        pass
    finally:
        return prices_and_quantity


def get_prices(link):
    if 'mobchasti' in link:
        result = get_mobchasti_prices_and_quantity(link)
        return result
    elif 'green-spark' in link:
        result = get_greenspark_prices_and_quantity(link)
        return result
    else:
        return None
