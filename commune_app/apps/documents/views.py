from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Document
from .serializers import DocumentSerializer, DocumentCreateSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().select_related('demande')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        return DocumentSerializer

    @action(detail=False, methods=['get'])
    def par_demande(self, request):
        demande_id = request.query_params.get('demande_id')
        if not demande_id:
            return Response({'error': 'demande_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        documents = self.get_queryset().filter(demande_id=demande_id)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)
