from django import forms
from ..models import Category


class CategoryAdminForm(forms.ModelForm):
    # Add a field to upload files
    image_upload = forms.FileField(required=False, label="Upload Image")

    class Meta:
        model = Category
        fields = ['seller', 'name', 'description', 'parent_category', 'is_active', 'image_upload']

    def save(self, commit=True):
        # Override save method to handle BinaryField
        instance = super().save(commit=False)
        
        # Handle file upload if provided
        image_file = self.cleaned_data.get('image_upload')
        if image_file:
            instance.image = image_file.read()  # Convert file to binary data

        if commit:
            instance.save()

        return instance