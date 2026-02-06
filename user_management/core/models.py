"""
Core base models with common fields and methods.

These abstract models provide common functionality that can be inherited by other models.
"""
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model with automatic created and updated timestamps.
    
    Adds:
        - created_at: Timestamp when the record was created
        - updated_at: Timestamp when the record was last updated (auto-updates)
        
    Usage:
        class MyModel(TimeStampedModel):
            # your fields here
            pass
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']  # Default ordering by newest first


class SoftDeleteModel(models.Model):
    """
    Abstract base model for soft deletion functionality.
    
    Instead of actually deleting records, marks them as deleted.
    This allows for data recovery and maintaining referential integrity.
    
    Adds:
        - is_deleted: Boolean flag to mark if record is deleted
        - deleted_at: Timestamp when the record was soft-deleted
        
    Methods:
        - soft_delete(): Mark the record as deleted
        - restore(): Restore a soft-deleted record
    """
    is_deleted = models.BooleanField(
        default=False,
        help_text="Indicates if this record is soft-deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the record was soft-deleted"
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Soft delete the object by marking it as deleted.
        Does not remove from database.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """
        Restore a soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Comprehensive base model combining timestamps and soft deletion.
    
    Inherits from both TimeStampedModel and SoftDeleteModel to provide
    full audit trail and soft deletion capabilities.
    
    Use this when you need both timestamp tracking and soft deletion.
    """
    class Meta:
        abstract = True
