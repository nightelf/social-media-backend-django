from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common import exceptions as err

from .models import Follow, User
from .serializers import MeSerializer, PublicUserSerializer


class MeView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user).data)


class PublicProfileView(APIView):
    def get(self, request, username):
        user = User.objects.filter(username=username, is_active=True).first()
        if not user:
            raise err.not_found("No such user.")
        return Response(PublicUserSerializer(user, context={"request": request}).data)


class FollowView(APIView):
    permission_classes = [IsAuthenticated]

    def _target(self, username, request):
        user = User.objects.filter(username=username, is_active=True).first()
        if not user:
            raise err.not_found("No such user.")
        if user == request.user:
            raise err.ContractError("validation_error", "You cannot follow yourself.", 422)
        return user

    def post(self, request, username):
        target = self._target(username, request)
        Follow.objects.get_or_create(follower=request.user, followed=target)
        return Response({"is_following": True, "followers_count": target.followers_count}, status=201)

    def delete(self, request, username):
        target = self._target(username, request)
        Follow.objects.filter(follower=request.user, followed=target).delete()
        return Response({"is_following": False, "followers_count": target.followers_count})
