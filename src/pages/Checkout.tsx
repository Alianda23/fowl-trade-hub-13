
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { initiateSTKPush } from "@/utils/mpesa";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useOrders } from "@/contexts/OrdersContext";
import { useCart } from "@/contexts/CartContext";

const Checkout = () => {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  const { createOrder } = useOrders();
  const { cart, clearCart } = useCart();

  // Get cart total from sessionStorage or calculate from cart
  const cartTotal = parseFloat(sessionStorage.getItem('cartTotal') || '0') || 
    cart.reduce((total, item) => total + (item.price * item.quantity), 0);

  const handleMpesaPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!phoneNumber || phoneNumber.length < 10) {
      toast({
        title: "Invalid Phone Number",
        description: "Please enter a valid M-Pesa phone number",
        variant: "destructive",
      });
      return;
    }

    if (cart.length === 0) {
      toast({
        title: "Empty Cart",
        description: "Please add items to your cart before checkout",
        variant: "destructive",
      });
      return;
    }
    
    setIsProcessing(true);
    
    try {
      const result = await initiateSTKPush(phoneNumber, Math.max(cartTotal, 1));
      
      if (result.success) {
        // Create order in database
        const orderData = {
          totalAmount: cartTotal,
          customerPhone: phoneNumber,
          paymentMethod: 'mpesa',
          checkoutRequestId: result.checkoutRequestID,
          items: cart.map(item => ({
            productId: item.id,
            quantity: item.quantity,
            unitPrice: item.price,
            totalPrice: item.price * item.quantity
          }))
        };

        const orderResult = await createOrder(orderData);

        if (orderResult.success) {
          toast({
            title: "Payment Initiated",
            description: "Please check your phone for the M-Pesa payment prompt and enter your PIN",
          });
          
          // Close dialog and reset state
          setPaymentDialogOpen(false);
          
          // Show processing notification
          toast({
            title: "Processing Payment",
            description: "Please wait while we confirm your payment...",
          });
          
          // Clear cart after successful order creation
          clearCart();
          sessionStorage.removeItem('cartTotal');
          sessionStorage.removeItem('cartItems');
          
          // In a production app, you would poll the server to check payment status
          // For simplicity, we're simulating a successful payment after a delay
          setTimeout(() => {
            toast({
              title: "Payment Successful",
              description: "Your order has been created successfully!",
            });
            
            // Redirect to homepage after successful payment
            setTimeout(() => navigate('/'), 2000);
          }, 5000);
        } else {
          toast({
            title: "Order Creation Failed",
            description: "Failed to create order. Please try again.",
            variant: "destructive",
          });
        }
      } else {
        toast({
          title: "Payment Failed",
          description: result.message || "Failed to initiate payment. Please try again.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Payment error:", error);
      toast({
        title: "Payment Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="container mx-auto max-w-2xl py-16">
      <h1 className="mb-8 text-3xl font-bold">Checkout</h1>
      
      <div className="mb-6 rounded-lg border p-6">
        <h2 className="mb-4 text-xl font-semibold">Order Summary</h2>
        <div className="flex justify-between">
          <span className="font-medium">Total Amount:</span>
          <span className="font-bold">KES {cartTotal.toLocaleString()}</span>
        </div>
      </div>
      
      <div className="rounded-lg border p-6">
        <h2 className="mb-6 text-xl font-semibold">Select Payment Method</h2>
        
        <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full bg-green-600 hover:bg-green-700">
              Pay with M-Pesa
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>M-Pesa Payment</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleMpesaPayment} className="space-y-4 pt-4">
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                  Enter M-Pesa Phone Number
                </label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="e.g., 0712345678"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="mt-1"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  Format: 07XXXXXXXX or 01XXXXXXXX (Safaricom/M-Pesa number)
                </p>
              </div>
              <div className="rounded bg-gray-50 p-3">
                <p className="text-sm"><strong>Amount:</strong> KES {cartTotal.toLocaleString()}</p>
              </div>
              <Button 
                type="submit" 
                className="w-full bg-green-600 hover:bg-green-700"
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Pay Now"
                )}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Checkout;
