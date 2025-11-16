from rest_framework import serializers
from .admin_models import Investment, InvestmentDocument

class InvestmentDocumentSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = InvestmentDocument
        fields = ['id', 'document_type', 'title', 'document_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'document_url']
    
    def get_document_url(self, obj):
        if obj.document and hasattr(obj.document, 'url') and obj.document.name:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None

class InvestmentSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    investment_type_display = serializers.CharField(source='get_investment_type_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    def get_documents(self, obj):
        # Safely get documents that have an associated file using the correct related name
        valid_documents = []
        for doc in obj.investment_documents.all():
            try:
                # This will raise an error if the file doesn't exist
                if doc.document and hasattr(doc.document, 'url') and doc.document.name:
                    valid_documents.append(doc)
            except (ValueError, AttributeError):
                continue
        
        # Use the document serializer for valid documents only
        return InvestmentDocumentSerializer(
            valid_documents,
            many=True,
            context=self.context
        ).data
    
    class Meta:
        model = Investment
        fields = [
            'id', 'title', 'description', 'investment_type', 'investment_type_display',
            'status', 'status_display', 'risk_level', 'risk_level_display',
            'minimum_amount', 'target_amount', 'current_price', 'current_amount',
            'expected_return_rate', 'start_date', 'end_date', 'duration_months',
            'location', 'available_to_all_vikoba', 'created_at', 'updated_at',
            'documents'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_amount']
