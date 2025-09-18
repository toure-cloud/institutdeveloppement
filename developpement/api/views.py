from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import TeamMember
from ..serializers import TeamMemberSerializer

class TeamMemberDetailAPI(APIView):
    def get(self, request, pk):
        member = get_object_or_404(TeamMember, pk=pk)
        serializer = TeamMemberSerializer(member, context={"request": request})
        return Response(serializer.data)
