﻿using RMS_API.Data.Orders;

namespace RMS_API.Models.Orders
{
    public class OrderModel
    {
        public int OrderId { get; set; }
        public int TableNumber { get; set; }
        public int? WaiterId { get; set; }
        public string OrderStatus { get; set; }

        public ICollection<OrderDetailsModel> OrderDetails { get; set; }
    }
}
