from users.models import User

# 설문 문항별 가중치 설정
WEIGHTS = {
    'preferred_time': 8,
    'conversation_style': 7,
    'important_points': 6,
    'noise_level': 9,
    'meal_preference': 5,
    'space_sharing_preference': 6,
    'pet_preference': 10,
    'smoking_preference': 10,
    'weekend_preference': 4,
}

# 총 가중치 합산
TOTAL_WEIGHT = sum(WEIGHTS.values())

def calculate_matching_score(youth_user: User, owner_user: User) -> int:
    if not all([youth_user, owner_user]):
        return 0

    score = 0

    # 1. 일치 여부로 점수를 계산하는 항목들
    simple_match_fields = [
        'preferred_time', 'conversation_style', 'meal_preference',
        'space_sharing_preference', 'pet_preference', 'smoking_preference',
        'weekend_preference'
    ]

    for field in simple_match_fields:
        youth_value = getattr(youth_user, field)
        owner_value = getattr(owner_user, field)
        if youth_value == owner_value:
            score += WEIGHTS[field]

    # 2. 중요한 점 (important_points) - 다중 선택 로직
    youth_points = set(youth_user.important_points.split(',') if youth_user.important_points else [])
    owner_points = set(owner_user.important_points.split(',') if owner_user.important_points else [])

    if youth_points or owner_points:
        match_count = len(youth_points.intersection(owner_points))
        # 두 사용자 중 선택 개수가 더 많은 쪽을 기준으로 일치율 계산
        max_choices = max(len(youth_points), len(owner_points))
        if max_choices > 0:
            score += (match_count / max_choices) * WEIGHTS['important_points']
    elif not youth_points and not owner_points:
        # 둘 다 항목을 선택하지 않은 경우, 어느 정도의 일치로 간주
        score += WEIGHTS['important_points'] * 0.5

    # 3. 소음 발생 (noise_level) - 차이 기반 로직
    noise_mapping = {'A': 0, 'B': 1, 'C': 2}
    if youth_user.noise_level and owner_user.noise_level:
        diff = abs(noise_mapping[youth_user.noise_level] - noise_mapping[owner_user.noise_level])
        # 차이가 클수록 점수를 덜 주는 방식
        # 2개 차이 -> 0점, 1개 차이 -> 4.5점, 0개 차이 -> 9점
        score += (2 - diff) / 2 * WEIGHTS['noise_level']

    # 최종 점수 계산 및 반올림
    normalized_score = (score / TOTAL_WEIGHT) * 100
    return round(normalized_score)


def get_matching_details(user1: User, user2: User):
    FIELD_LABELS = {
        'preferred_time': '생활리듬',
        'conversation_style': '대화스타일',
        'important_points': '중요한점',
        'noise_level': '소음수준',
        'meal_preference': '식사',
        'space_sharing_preference': '공간공유',
        'pet_preference': '반려동물',
        'smoking_preference': '흡연',
        'weekend_preference': '주말성향',
    }

    # 점수 구간별 매칭 문구
    def get_matching_text(score):
        if score >= 90:
            return "매우 잘 맞음 👍"
        elif score >= 70:
            return "잘 맞음 😊"
        elif score >= 50:
            return "보통 😐"
        else:
            return "조금 다름 🧐"

    matching_score = calculate_matching_score(user1, user2)
    matching_text = get_matching_text(matching_score)

    # 1. 일치하는 항목 중 가중치가 높은 상위 2개 찾기
    matched_fields = {}

    # 필드 일치 여부 확인
    for field in WEIGHTS:
        if field == 'important_points':
            user1_points = set(user1.important_points.split(',') if user1.important_points else set())
            user2_points = set(user2.important_points.split(',') if user2.important_points else set())
            if user1_points.intersection(user2_points):
                matched_fields['important_points'] = WEIGHTS['important_points']
            continue

        if field == 'noise_level':
            if user1.noise_level == user2.noise_level:
                matched_fields['noise_level'] = WEIGHTS['noise_level']
            continue

        if getattr(user1, field) == getattr(user2, field):
            matched_fields[field] = WEIGHTS[field]

    # 가중치가 높은 순서로 정렬하여 상위 2개 항목 추출
    top_matches = sorted(matched_fields, key=lambda f: WEIGHTS[f], reverse=True)[:2]

    # 설명 문구 생성
    top_match_names = [FIELD_LABELS[f] for f in top_matches]
    explanation = ""
    if len(top_match_names) >= 2:
        explanation = f"'{top_match_names[0]}'와 '{top_match_names[1]}'이 잘 맞아요."
    elif len(top_match_names) == 1:
        explanation = f"'{top_match_names[0]}'이 잘 맞아요."
    else:
        explanation = "두 분의 성향 중 잘 맞는 부분이 잘 드러나지 않아요."

    # 2. 잘 맞는 해시태그 3가지 생성
    hashtags = []

    # 활동 시간대
    if user1.preferred_time == user2.preferred_time:
        if user1.preferred_time == 'A':
            hashtags.append('아침형')
        else:
            hashtags.append('저녁형')

    # 대화 스타일
    if user1.conversation_style == user2.conversation_style:
        if user1.conversation_style == 'A':
            hashtags.append('조용함')
        else:
            hashtags.append('활발함')

    # 중요한 점 (다중 선택)
    user1_points = set(user1.important_points.split(',') if user1.important_points else set())
    user2_points = set(user2.important_points.split(',') if user2.important_points else set())
    for choice in user1_points.intersection(user2_points):
        if choice == 'A':
            hashtags.append('깔끔한')
        elif choice == 'B':
            hashtags.append('생활리듬')
        elif choice == 'C':
            hashtags.append('소통')
        elif choice == 'D':
            hashtags.append('배려심')
        else:
            hashtags.append('사생활존중')

    # 식사
    if user1.meal_preference == user2.meal_preference:
        if user1.meal_preference == 'A':
            hashtags.append('함께식사')
        else:
            hashtags.append('각자식사')

    # 주말
    if user1.weekend_preference == user2.weekend_preference:
        if user1.weekend_preference == 'A':
            hashtags.append('집콕')
        else:
            hashtags.append('외출')

    # 흡연
    if user1.smoking_preference == user2.smoking_preference:
        if user1.smoking_preference == 'A':
            hashtags.append('흡연')
        else:
            hashtags.append('비흡연')

    # 소음 발생
    if user1.noise_level == user2.noise_level:
        if user1.noise_level == 'A':
            hashtags.append('소음가능')
        elif user1.noise_level == 'B':
            hashtags.append('소음일부가능')
        else:
            hashtags.append('소음불가')

    # 공간 공유
    if user1.space_sharing_preference == user2.space_sharing_preference:
        if user1.space_sharing_preference == 'A':
            hashtags.append('공용활발')
        elif user1.space_sharing_preference == 'B':
            hashtags.append('공용적당')
        else:
            hashtags.append('공용적음')

    # 반려동물
    if user1.pet_preference == user2.pet_preference:
        if user1.pet_preference == 'A':
            hashtags.append('반려동물과')
        else:
            hashtags.append('반려동물없이')

    # 중복 제거 및 최대 3개만 선택
    hashtags = list(dict.fromkeys(hashtags))[:3]

    return {
        'matching_score': matching_score,
        'matching_text': matching_text,
        'explanation': explanation,
        'hashtags': hashtags,
    }