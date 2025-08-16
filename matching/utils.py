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

    # 1. 활동 시간대 (preferred_time)
    if youth_user.preferred_time == owner_user.preferred_time:
        score += WEIGHTS['preferred_time']

    # 2. 대화 스타일 (conversation_style)
    if youth_user.conversation_style == owner_user.conversation_style:
        score += WEIGHTS['conversation_style']

    # 3. 중요한 점 (important_points)
    if youth_user.important_points == owner_user.important_points:
        score += WEIGHTS['important_points']

    # 4. 소음 발생 (noise_level)
    # A=항상, B=특정, C=거의안함 -> 차이가 적을수록 점수 높게
    diff = abs(ord(youth_user.noise_level) - ord(owner_user.noise_level))
    score += (2 - diff) * (WEIGHTS['noise_level'] / 2)

    # 5. 식사 (meal_preference)
    if youth_user.meal_preference == owner_user.meal_preference:
        score += WEIGHTS['meal_preference']

    # 6. 공간 공유 (space_sharing_preference)
    if youth_user.space_sharing_preference == owner_user.space_sharing_preference:
        score += WEIGHTS['space_sharing_preference']

    # 7. 반려동물 (pet_preference)
    if youth_user.pet_preference == owner_user.pet_preference:
        score += WEIGHTS['pet_preference']

    # 8. 흡연 (smoking_preference)
    if youth_user.smoking_preference == owner_user.smoking_preference:
        score += WEIGHTS['smoking_preference']

    # 9. 주말 (weekend_preference)
    if youth_user.weekend_preference == owner_user.weekend_preference:
        score += WEIGHTS['weekend_preference']

    # 총점 계산 (0~100점 범위)
    # 매칭 점수 = Σ(문항별 일치 점수 x 가중치) / Σ(가중치) x 100
    normalized_score = (score / TOTAL_WEIGHT) * 100
    return round(normalized_score)