# backend-order-service

Order Service
Handles the entire lifecycle of customer orders. It manages order creation, status tracking (e.g., pending, shipped, delivered), item details, quantities, pricing, and total amounts. This service validates orders, updates inventory status, and maintains the relationship between users and their purchased items.

Payment Service
Processes payment transactions for orders. It supports multiple payment methods (credit cards, PayPal, etc.), tracks payment status (pending, completed, refunded), and manages transaction details including currency, amounts, and refunds. This service integrates with external payment gateways securely and ensures financial data integrity and compliance.

Support order cancellation and refund requests
