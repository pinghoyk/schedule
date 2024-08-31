import requests
from bs4 import BeautifulSoup


def schedule(URL): # расписание
    url = URL
    response = requests.get(url)
    
    # Словарь для хранения данных
    schedule_dict = {}
    
    if response.status_code == 200:
        # Парсим содержимое страницы
        soup = BeautifulSoup(response.text, 'html.parser')
    
        schedule = soup.find('div', class_='timetableContainer') # вся неделя
        days = schedule.find_all('td', attrs={'style': True}) # все дни
    
        for day in days:
            day_week = day.find('div', class_='dayHeader').text.strip()
            day_schedule = day.find('div', attrs={'style': 'padding-left: 6px;'}) # расписание дня
            
            # Список для хранения информации о занятиях в этот день
            lessons_list = []
    
            lessons = day_schedule.find_all('div', class_='lessonBlock') # блок пар
            for lesson in lessons:
                lesson_time_block = lesson.find('div', class_='lessonTimeBlock').text.strip().split('\n')
                lesson_number = lesson_time_block[0].strip()
                lesson_time_start = lesson_time_block[1].strip()
                lesson_time_finish = lesson_time_block[2].strip()
                
                try:
                    lesson_name = lesson.find('div', class_='discHeader').text.strip()
                except:
                    lesson_name = "Пары нет"
                
                # Собираем информацию о паре
                lesson_info = {
                    'number': lesson_number,
                    'time_start': lesson_time_start,
                    'time_finish': lesson_time_finish,
                    'name': lesson_name,
                    'data': []
                }
    
                # Находим все блоки discSubgroup, содержащие информацию о преподавателях и кабинетах
                lesson_teachers_data = lesson.find_all('div', class_='discSubgroup')
                for subgroup in lesson_teachers_data:
                    teacher = subgroup.find('div', class_='discSubgroupTeacher').text.strip()
                    classroom = subgroup.find('div', class_='discSubgroupClassroom').text.strip()
                    lesson_info['data'].append({
                        'teacher': teacher,
                        'classroom': classroom
                    })
    
                lessons_list.append(lesson_info)
    
            # Добавляем информацию о занятиях в словарь с ключом день недели
            schedule_dict[day_week] = lessons_list
    
    else:
        schedule_dict['Ошибка'] = f"Ошибка при запросе: {response.status_code}"
    
    return schedule_dict

def table_courses(url): # получение всех групп и курсов
    response = requests.get(url)
    
    # Парсим содержимое страницы
    soup = BeautifulSoup(response.text, 'html.parser')
    courses = soup.find_all('div', class_='spec-year-block-container')
    
    # Словарь для хранения курсов и их групп
    course_dict = {}
    
    # Перебираем все контейнеры курсов
    for course in courses:
        spec_course_blocks = course.find_all('div', class_='spec-year-block')
        for spec_course in spec_course_blocks:
            year_name = spec_course.find('span', class_='spec-year-name').text.strip()
            year_name = year_name.replace(":",'')
    
            # Инициализируем пустой словарь для групп текущего курса
            if year_name not in course_dict:
                course_dict[year_name] = {}
    
            groups = spec_course.find_all('span', class_='group-block')
            for group in groups:
                group_link_tag = group.find('a')
                group_name = group_link_tag.text.strip()
                group_link = group_link_tag['href'].strip()
    
                # Добавляем группу и ссылку в словарь
                course_dict[year_name][group_name] = group_link
    return course_dict


