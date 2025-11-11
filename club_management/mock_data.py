# club_management/mock_data.py

# 모임 탐색 페이지에 사용될 Mock 데이터 리스트
CLUBS_MOCK_DATA = [
    {
        'id': 1,
        'title': '주말 농구 팀 \'슬램덩커스\'',
        'description': '실력과 상관없이 농구를 사랑하는 모든 분들을 환영합니다. 매주 토요일 정기 모임!',
        'category': '체육 🏀',
        'region': '서울/경기',
        'members': 12,
        'badge_class': 'bg-blue-100 text-blue-600'
    },
    {
        'id': 2,
        'title': '퇴근 후 힐링 드로잉',
        'description': '매주 수요일 저녁, 따뜻한 카페에서 함께 그림을 그리며 하루를 마무리해요. 오일 파스텔 사용.',
        'category': '미술/공예 🎨',
        'region': '강남구',
        'members': 8,
        'badge_class': 'bg-pink-100 text-pink-600'
    },
    {
        'id': 3,
        'title': '월간 독서 모임 \'책갈피\'',
        'description': '한 달에 한 권, 인문학/소설을 함께 읽고 토론합니다. 조용한 독서를 즐기는 분들 환영.',
        'category': '독서 📚',
        'region': '마포/홍대',
        'members': 25,
        'badge_class': 'bg-indigo-100 text-indigo-600'
    },
    {
        'id': 4,
        'title': '초보자를 위한 홈 베이킹',
        'description': '쉬운 쿠키부터 케이크까지, 주말 오전에 함께 만들어봐요! 장비 일체 제공.',
        'category': '요리/베이커리 🧑‍🍳',
        'region': '분당',
        'members': 5,
        'badge_class': 'bg-yellow-100 text-yellow-600'
    }
]



# 모임 상세 페이지에 사용될 Mock 데이터 딕셔너리
GROUP_DETAIL_MOCK_DATA = {
    1: { # 주말 농구 팀 '슬램덩커스'
        'name': "주말 농구 팀 '슬램덩커스'", 'category': "체육 🏀", 'region': "서울/경기", 'members': 12,
        'description': "저희 슬램덩커스는 실력에 상관없이 농구를 사랑하는 모든 분들을 환영합니다. 매주 토요일 정기 모임을 통해 친목을 다지고 건강한 땀을 흘리고 있습니다. 단순한 운동을 넘어, 팀워크와 열정을 함께 나누는 모임이 되겠습니다.",
        'activities': [
            {'title': '정기 연습: 3점 슛 마스터', 'date': '2025.12.01 (일) 15:00', 'fee': '5,000원', 'status': '참석', 'attendees': 10},
            {'title': '친선 경기: 이웃 팀과의 대결', 'date': '2025.11.24 (일) 14:00', 'fee': '10,000원', 'status': '마감', 'attendees': 12},
            ],
            'leader_nickname': '농구왕 리더',   
            'leader_id': 'leader123'
        
    },
    2: { # 퇴근 후 힐링 드로잉
        'name': "퇴근 후 힐링 드로잉", 'category': "미술/공예 🎨", 'region': "강남구", 'members': 8,
        'description': "매주 수요일 저녁, 따뜻한 카페에서 함께 그림을 그리며 하루를 마무리해요. 오일 파스텔, 색연필 등 다양한 재료를 시도해 볼 수 있습니다. 장비가 없어도 괜찮아요. 함께 힐링하실 분들을 기다립니다.",
        'activities': [
            {'title': '11월 정기 드로잉: 크리스마스', 'date': '2025.11.27 (수) 19:30', 'fee': '재료비 15,000원', 'status': '참석', 'attendees': 6},
            {'title': '갤러리 투어: 이달의 전시', 'date': '2025.12.14 (토) 11:00', 'fee': '5,000원', 'status': '참석', 'attendees': 3},
            ],
            'leader_nickname': '아티스트 엘라',
            'leader_id': 'artist_ella'
    },
    3: { # 월간 독서 모임 '책갈피'
        'name': "월간 독서 모임 '책갈피'", 'category': "독서 📚", 'region': "마포/홍대", 'members': 25,
        'description': "한 달에 한 권, 인문학/소설을 함께 읽고 토론합니다. 조용하고 진중한 독서를 즐기는 분들을 위한 모임입니다. 커피 한 잔과 함께 지적인 성장을 나눠요.",
        'activities': [
            {'title': '12월 도서 토론: ' + "'데미안'", 'date': '2025.12.10 (화) 20:00', 'fee': '무료', 'status': '참석', 'attendees': 18},],
            'leader_nickname': '독서왕이다',
            'leader_id': 'book_king',
    },
    4: { # 초보자를 위한 홈 베이킹
        'name': "초보자를 위한 홈 베이킹", 'category': "요리/베이커리 🧑‍🍳", 'region': "분당", 'members': 5,
        'description': "쉬운 쿠키부터 케이크까지, 주말 오전에 함께 만들어봐요! 베이킹의 즐거움을 함께 나누실 초보자 분들을 환영합니다. 모든 장비는 모임에서 제공합니다.",
        'activities': [
            {'title': '크리스마스 케이크 만들기', 'date': '2025.12.21 (토) 10:00', 'fee': '재료비 20,000원', 'status': '마감', 'attendees': 5},
            {'title': '쉬운 쿠키 굽기', 'date': '2025.12.28 (토) 10:00', 'fee': '재료비 10,000원', 'status': '참석', 'attendees': 2},
            ],
            'leader_nickname': '빵빠라',
            'leader_id': 'bang',
    }
}
