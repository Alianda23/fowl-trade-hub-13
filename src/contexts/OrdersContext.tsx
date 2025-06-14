
import { createContext, useState, useContext, useEffect, ReactNode } from "react";
import { Product } from "@/data/products";
import { CartItem } from "./CartContext";

// Define Order interface
export interface Order {
  id: string;
  products: CartItem[];
  status: string;
  date: string;
  total: number;
}

// Define the shape of our context
interface OrdersContextType {
  orders: Order[];
  setOrders: React.Dispatch<React.SetStateAction<Order[]>>;
  showOrders: boolean;
  setShowOrders: (show: boolean) => void;
  fetchOrders: () => Promise<void>;
  createOrder: (orderData: any) => Promise<{ success: boolean; orderId?: string; orderNumber?: string }>;
}

// Create the context with a default value
const OrdersContext = createContext<OrdersContextType | undefined>(undefined);

// Provider component
export const OrdersProvider = ({ children }: { children: ReactNode }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [showOrders, setShowOrders] = useState(false);

  const fetchOrders = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/orders/user', {
        method: 'GET',
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setOrders(data.orders || []);
      } else {
        console.error("Failed to fetch orders:", data.message);
      }
    } catch (error) {
      console.error("Error fetching orders:", error);
    }
  };

  const createOrder = async (orderData: any) => {
    try {
      const response = await fetch('http://localhost:5000/api/orders/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(orderData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh orders after creating new one
        await fetchOrders();
      }
      
      return data;
    } catch (error) {
      console.error("Error creating order:", error);
      return { success: false };
    }
  };

  // Fetch orders when component mounts and user might be authenticated
  useEffect(() => {
    fetchOrders();
  }, []);

  const value = {
    orders,
    setOrders,
    showOrders,
    setShowOrders,
    fetchOrders,
    createOrder
  };

  return <OrdersContext.Provider value={value}>{children}</OrdersContext.Provider>;
};

// Custom hook to use the orders context
export const useOrders = () => {
  const context = useContext(OrdersContext);
  if (context === undefined) {
    throw new Error("useOrders must be used within an OrdersProvider");
  }
  return context;
};
