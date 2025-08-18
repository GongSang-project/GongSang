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