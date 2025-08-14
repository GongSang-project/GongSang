from django.shortcuts import render, get_object_or_404
from .models import Room


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    owner = room.owner

    # 설문조사 결과를 바탕으로 해시태그 리스트 생성
    hashtags = []
    # 활동 시간대
    if owner.preferred_time == 'A':
        hashtags.append('아침형')
    else:
        hashtags.append('저녁형')
    # 중요한 점
    if owner.important_points == 'A':
        hashtags.append('깔끔한')
    elif owner.important_points == 'B':
        hashtags.append('생활리듬')
    elif owner.important_points == 'C':
        hashtags.append('소통')
    elif owner.important_points == 'D':
        hashtags.append('배려심')
    else:
        hashtags.append('사생활존중')
    # 대화 스타일
    if owner.conversation_style == 'A':
        hashtags.append('조용함')
    else:
        hashtags.append('활발함')

    context = {
        'room': room,
        'hashtags': hashtags,  # 템플릿으로 전달
    }
    return render(request, 'room_detail.html', context)