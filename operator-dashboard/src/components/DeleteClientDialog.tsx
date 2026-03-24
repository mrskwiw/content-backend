import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, Download } from 'lucide-react';

interface DeleteClientDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: string;
  clientName: string;
  onConfirmDelete: () => Promise<void>;
  onExportData?: () => Promise<void>;
}

export function DeleteClientDialog({
  open,
  onOpenChange,
  clientId,
  clientName,
  onConfirmDelete,
  onExportData,
}: DeleteClientDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [hasExported, setHasExported] = useState(false);

  const handleExport = async () => {
    if (onExportData) {
      await onExportData();
      setHasExported(true);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onConfirmDelete();
      onOpenChange(false);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            Delete Client - GDPR/CCPA Compliance
          </DialogTitle>
          <DialogDescription>
            You are about to delete <strong>{clientName}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Nuclear Purge Warning:</strong> Due to database limitations,
              this deletion request may trigger a FULL DATABASE PURGE affecting ALL
              clients. While we prioritize soft deletion, compliance requirements
              may necessitate complete data destruction.
            </AlertDescription>
          </Alert>

          <div className="space-y-2 text-sm">
            <h4 className="font-medium">What will be deleted:</h4>
            <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
              <li>Client profile and contact information</li>
              <li>All projects and generated content</li>
              <li>Research results and analytics data</li>
              <li>Post history and deliverables</li>
            </ul>
          </div>

          <div className="space-y-2 text-sm">
            <h4 className="font-medium">Recovery Options:</h4>
            <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
              <li>Data can be restored within 90 days</li>
              <li>After 90 days, data is permanently purged</li>
              <li>Export your data before deletion (recommended)</li>
            </ul>
          </div>

          {onExportData && !hasExported && (
            <Button
              variant="outline"
              className="w-full"
              onClick={handleExport}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data Before Deletion
            </Button>
          )}

          {hasExported && (
            <Alert>
              <AlertDescription>
                ✓ Data exported successfully. Safe to proceed with deletion.
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Client (Soft Delete)'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
