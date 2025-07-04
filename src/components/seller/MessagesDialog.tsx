
// Update backend route of marking message as read in the MessagesDialog component
// This component already exists, we're just adding some code to handle the notification badge correctly

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useEffect, useState } from "react";

interface Message {
  id: string;
  senderName: string;
  senderEmail: string;
  message: string;
  productName: string;
  isRead: boolean;
  createdAt: string;
}

interface MessagesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onMessagesLoaded: (unreadCount: number) => void;
}

const MessagesDialog = ({ open, onOpenChange, onMessagesLoaded }: MessagesDialogProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  
  const fetchMessages = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/seller/messages', {
        method: 'GET',
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setMessages(data.messages || []);
        
        // Count unread messages
        const unreadCount = data.messages.filter((msg: Message) => !msg.isRead).length;
        onMessagesLoaded(unreadCount);
      } else {
        toast({
          title: "Error",
          description: "Failed to fetch messages",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    if (open) {
      fetchMessages();
    }
  }, [open]);
  
  const handleMarkAsRead = async (messageId: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/seller/messages/mark-read/${messageId}`, {
        method: 'PUT',
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update the message in the list
        setMessages(messages.map(msg => 
          msg.id === messageId ? { ...msg, isRead: true } : msg
        ));
        
        // Update the unread count
        const updatedUnreadCount = messages.filter(msg => 
          msg.id !== messageId && !msg.isRead
        ).length;
        
        onMessagesLoaded(updatedUnreadCount);
      } else {
        toast({
          title: "Error",
          description: "Failed to mark message as read",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error marking message as read:", error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[625px]">
        <DialogHeader>
          <DialogTitle>Customer Messages</DialogTitle>
        </DialogHeader>
        
        {isLoading ? (
          <div className="flex justify-center py-8">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="py-8 text-center text-gray-500">No messages yet.</div>
        ) : (
          <div className="max-h-[400px] overflow-y-auto space-y-4">
            {messages.map((message) => (
              <div 
                key={message.id}
                className={`rounded-lg border p-4 ${!message.isRead ? 'bg-sage-50 border-sage-200' : ''}`}
              >
                <div className="mb-2 flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{message.senderName}</p>
                    <p className="text-sm text-gray-500">{message.senderEmail}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {new Date(message.createdAt).toLocaleString()}
                    </p>
                    {!message.isRead && (
                      <Button 
                        variant="outline"
                        size="sm"
                        className="mt-1 h-6 text-xs"
                        onClick={() => handleMarkAsRead(message.id)}
                      >
                        Mark as Read
                      </Button>
                    )}
                  </div>
                </div>
                <p className="mb-2 text-sm text-gray-600">
                  <span className="font-medium">About:</span> {message.productName}
                </p>
                <p>{message.message}</p>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default MessagesDialog;
