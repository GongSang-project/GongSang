from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, Http404
from room.models import Room
from users.models import User
from .models import ChatRoom, Message
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import ChatRoom, Message
import json
from django.shortcuts import redirect

@login_required
@require_POST
def create_or_get_chatroom(request):
    room_id = request.POST.get('room_id')

    # 필수 파라미터가 없으면 에러 반환
    if not room_id:
        return JsonResponse({'error': 'room_id가 필요합니다.'}, status=400)

    try:
        room = get_object_or_404(Room, id=room_id)
        current_user = request.user

        if current_user.is_youth:
            youth_user = current_user
            senior_user = room.owner
        else:  # 시니어인 경우
            senior_user = current_user
            youth_user = room.contracted_youth

            if youth_user is None:
                return JsonResponse({'error': '계약된 청년이 없어 채팅방을 만들 수 없습니다.'}, status=400)


    except Http404:
        return JsonResponse({'error': '존재하지 않는 방입니다.'}, status=404)

    if youth_user is None:
        return JsonResponse({'error': '채팅을 시작할 청년이 지정되지 않았습니다.'}, status=400)

    try:
        chatroom = ChatRoom.objects.get(room=room, youth=youth_user, senior=senior_user)
        is_new = False
    except ChatRoom.DoesNotExist:
        chatroom = ChatRoom.objects.create(room=room, youth=youth_user, senior=senior_user)
        is_new = True

    return JsonResponse({
        'chatroom_id': chatroom.id,
        'is_new': is_new,
        'message': '채팅방이 생성되었거나 기존 채팅방이 반환되었습니다.'
    })


@login_required
@require_POST
def send_message(request):
    try:
        # 클라이언트에서 보낸 JSON 데이터를 파싱
        data = json.loads(request.body)
        chatroom_id = data.get('chatroom_id')
        content = data.get('content')

        # 필수 데이터 누락 시 에러 반환
        if not chatroom_id or not content:
            return JsonResponse({'error': '채팅방 ID와 메시지 내용이 필요합니다.'}, status=400)

        # ChatRoom 객체 가져오기 (없으면 404)
        chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

        # 메시지 생성 및 저장
        message = Message.objects.create(
            chatroom=chatroom,
            author=request.user,
            content=content
        )

        # 성공 시, 저장된 메시지 정보를 포함하여 JSON 응답 반환
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'author': message.author.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime("%H:%M")
            }
        }, status=200)

    except json.JSONDecodeError:
        # JSON 형식이 아닐 경우
        return JsonResponse({'error': '유효하지 않은 JSON 형식입니다.'}, status=400)
    except Exception as e:
        # 그 외 모든 예외에 대한 처리
        print(f"send_message 뷰에서 예상치 못한 오류 발생: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def get_messages(request, chatroom_id):
    try:
        chatroom = ChatRoom.objects.get(id=chatroom_id)
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': '채팅방이 존재하지 않습니다.'}, status=404)

    # 해당 채팅방의 모든 메시지 가져오기
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')

    # JSON 형태로 직렬화하여 반환
    messages_data = serializers.serialize('json', messages, fields=('author', 'content', 'timestamp'))

    return JsonResponse(messages_data, safe=False)

def chatroom_detail(request, chatroom_id):
    if not request.user.is_authenticated:
        return redirect('users:user_selection')

    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)
    messages = Message.objects.filter(chatroom=chatroom).order_by('timestamp')
    current_user = request.user
    other_user = chatroom.youth if chatroom.senior == current_user else chatroom.senior

    # --- 디버그 ---
    if request.user.is_authenticated:
        print(f"현재 로그인된 사용자: {request.user.username} (ID: {request.user.id}, 청년: {request.user.is_youth})")
    else:
        print("현재 로그인된 사용자가 없습니다.")
    # ------------------------------------

    context = {
        'chatroom': chatroom,
        'messages': messages,
        'room': chatroom.room,
        'current_user': current_user,
        'other_user': other_user,
    }
    return render(request, 'chat/chatroom.html', context)