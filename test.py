import requests
from bs4 import BeautifulSoup


url = 'https://pronew.chenk.ru/blocks/manage_groups/website/view.php?gr=327&dep=3'


response = requests.get(url)


if response.status_code == 200:
    # Парсим содержимое страницы
    soup = BeautifulSoup(response.text, 'html.parser') # хранение всего сайта

    schedule = soup.find('div', class_='timetableContainer') # вся недели
    days = schedule.find_all('td', attrs={'style': True}) # все дни

    day = days[1]

    day_week = day.find('div', class_='dayHeader') # день недели
    print(day_week.text)

    day_schedule = day.find('div', attrs={'style': 'padding-left: 6px;'}) # расписание дня

    lessons = day_schedule.find_all('div', class_='lessonBlock')  # блок пар
    for lesson in lessons:
        lesson_time_block = lesson.find('div', class_='lessonTimeBlock') # номер пары
        lesson_nubmer = (lesson_time_block.text)[1]

        lesson_time_start = (lesson_time_block.text).split('\n')[2]
        lesson_time_finish = (lesson_time_block.text).split('\n')[3]


        lesson_data = lesson.find('div', class_='discBlock')
        lesson_name = (lesson_data.text).split('\n')[2]
        lesson_teachers = (lesson_data.text).replace((lesson_name), '')

        print(lesson_nubmer)
        print(lesson_time_start, lesson_time_finish)
        print(lesson_name)
        print(lesson_teachers)


else:
    print(f"Ошибка при запросе: {response.status_code}")