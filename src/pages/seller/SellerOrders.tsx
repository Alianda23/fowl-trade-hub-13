
import { Button } from "@/components/ui/button";
import SellerSidebar from "@/components/seller/SellerSidebar";
import { 
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Truck, XCircle, ArrowLeft, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

interface SellerOrder {
  id: string;
  customerName: string;
  items: Array<{
    productName: string;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }>;
  status: 'pending' | 'confirmed' | 'dispatched' | 'delivered' | 'cancelled';
  paymentStatus: string;
  date: string;
  total: number;
}

const SellerOrders = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [orders, setOrders] = useState<SellerOrder[]>([]);
  
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check if user is authenticated in localStorage
        const storedAuth = localStorage.getItem('isSellerAuthenticated');
        const storedEmail = localStorage.getItem('sellerEmail');
        
        if (storedAuth === 'true' && storedEmail) {
          // Verify with backend
          const response = await fetch('http://localhost:5000/api/seller/check-auth', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include'
          });
          
          const data = await response.json();
          
          if (data.isAuthenticated) {
            setIsAuthenticated(true);
            fetchOrders();
          } else {
            // If backend says not authenticated, clear localStorage
            localStorage.removeItem('isSellerAuthenticated');
            localStorage.removeItem('sellerEmail');
          }
        }
      } catch (error) {
        console.error("Auth check error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [navigate, toast]);

  const fetchOrders = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/orders/seller', {
        method: 'GET',
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setOrders(data.orders || []);
      } else {
        toast({
          title: "Error",
          description: "Failed to fetch orders",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching orders:", error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    if (!isAuthenticated) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to update orders",
        variant: "destructive",
      });
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:5000/api/orders/${orderId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ status: newStatus })
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "Order Updated",
          description: `Order #${orderId} has been updated to ${newStatus}.`,
        });
        
        // Refresh orders
        fetchOrders();
      } else {
        toast({
          title: "Error",
          description: data.message || "Failed to update order",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error updating order:", error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleDispatch = (orderId: string) => {
    handleStatusUpdate(orderId, 'dispatched');
  };

  const handleCancel = (orderId: string) => {
    handleStatusUpdate(orderId, 'cancelled');
  };

  const getStatusBadge = (status: SellerOrder['status']) => {
    const statusStyles = {
      pending: "bg-yellow-100 text-yellow-800",
      confirmed: "bg-blue-100 text-blue-800",
      dispatched: "bg-purple-100 text-purple-800",
      delivered: "bg-green-100 text-green-800",
      cancelled: "bg-red-100 text-red-800"
    };

    return (
      <Badge variant="outline" className={statusStyles[status]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-sage-600" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <SellerSidebar />
      
      <main className="flex-1 bg-gray-50">
        <div className="border-b bg-white p-6">
          <div className="mb-4 flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/seller")}>
              <ArrowLeft className="h-5 w-5" />
              Back
            </Button>
            <h1 className="text-2xl font-bold">Orders</h1>
          </div>
          <p className="text-sm text-gray-600">Manage your customer orders</p>
          
          {!isAuthenticated && (
            <div className="mt-4 rounded-md bg-yellow-50 p-3 text-yellow-800">
              <p>Sign in to manage orders</p>
            </div>
          )}
        </div>

        <div className="p-6">
          {orders.length === 0 ? (
            <div className="rounded-lg border bg-white p-8 text-center">
              <p className="text-gray-500">No orders yet</p>
            </div>
          ) : (
            <div className="rounded-lg border bg-white">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Products</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Payment</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell>#{order.id}</TableCell>
                      <TableCell>{order.customerName}</TableCell>
                      <TableCell>
                        {order.items.map((item, index) => (
                          <div key={index} className="text-sm">
                            {item.productName} (x{item.quantity})
                          </div>
                        ))}
                      </TableCell>
                      <TableCell>KES {order.total.toLocaleString()}</TableCell>
                      <TableCell>{getStatusBadge(order.status)}</TableCell>
                      <TableCell>
                        <Badge variant={order.paymentStatus === 'completed' ? 'default' : 'destructive'}>
                          {order.paymentStatus}
                        </Badge>
                      </TableCell>
                      <TableCell>{order.date}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {(order.status === 'pending' || order.status === 'confirmed') && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                className="gap-1"
                                onClick={() => handleDispatch(order.id)}
                                disabled={!isAuthenticated}
                              >
                                <Truck className="h-4 w-4" />
                                Dispatch
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="gap-1 text-red-600 hover:bg-red-50"
                                onClick={() => handleCancel(order.id)}
                                disabled={!isAuthenticated}
                              >
                                <XCircle className="h-4 w-4" />
                                Cancel
                              </Button>
                            </>
                          )}
                          {!isAuthenticated && (order.status === 'pending' || order.status === 'confirmed') && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="gap-1"
                              onClick={() => navigate('/seller/login')}
                            >
                              Sign In to Manage
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          
          {!isAuthenticated && (
            <div className="mt-8 rounded-lg border bg-sage-50 p-6 text-center">
              <h3 className="mb-2 text-lg font-medium">Want to manage orders?</h3>
              <p className="mb-4 text-gray-600">Sign in or create a seller account to manage orders</p>
              <div className="flex justify-center gap-4">
                <Button onClick={() => navigate('/seller/login')}>Sign In</Button>
                <Button variant="outline" onClick={() => navigate('/seller/signup')}>Create Account</Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default SellerOrders;
