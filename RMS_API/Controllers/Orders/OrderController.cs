﻿using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Finance;
using RMS_API.Data.Orders;
using RMS_API.Data.Users;
using RMS_API.Models;
using RMS_API.Models.Orders;
using RMS_API.Models.Users;
using StackExchange.Redis;
using System.Security.Claims;

namespace RMS_API.Controllers.Orders
{
    [Route("api/{version:apiVersion}/[controller]")]
    [ApiController]
    [Authorize]
    public class OrderController : Controller
    {
        private readonly ApplicationDbContext _context;

        public OrderController(ApplicationDbContext context)
        {
            _context = context;
        }
        [HttpGet]
        // GET: OrderController
        public async Task<ActionResult<IEnumerable<OrderModel>>> Get()
        {
            try
            {
                var roles = await _context.Orders
                     .Select(ur => new OrderModel
                     {
                         OrderId = ur.OrderId,
                         OrderStatus = ur.OrderStatus,
                         TableNumber = ur.TableNumber,
                         WaiterId = ur.WaiterId,
                         TotalPrice = ur.OrderDetails.Sum(od => od.Price)
                     })
                    .ToListAsync();
                return Ok(roles);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        [HttpGet("{id}")]
        // GET: OrderController/Get/5
        public async Task<ActionResult<OrderDetails>> Get(int id)
    {
        try
        {
                var orderDetails = await _context.Orders
                                    .Include(o => o.OrderDetails)
                                    .Where(o=> o.OrderId==id)
                                    .Select(o => new OrderWithDetails
                                    {
                                        OrderId = o.OrderId,
                                        TableNumber=o.TableNumber,
                                        OrderDetails= o.OrderDetails.Select(od => new OrderDetailsModel
                                        {
                                            MenuId= (int)od.MenuId,
                                            OrderDetailId=od.OrderDetailId,
                                            OrderId=od.OrderId,
                                            Quantity=od.Quantity,
                                            Price=od.Price

                                        }).ToList()
                                    })
                                    .FirstOrDefaultAsync();

            if (orderDetails == null)
            {
                return NotFound($"Order with ID {id} not found.");
            }

            return Ok(orderDetails);
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }


        [HttpPost]
        [Authorize]
        public async Task<IActionResult> Post([FromBody] OrderModel order)
        {
            try
            {
                using (var transaction = await _context.Database.BeginTransactionAsync())
                {
                    try
                    {
                        var authenticatedUser = HttpContext.Items["User"] as AuthenticatedUser;
                        var userId = Convert.ToInt32(authenticatedUser?.UserId);

                        var orderMaster = new OrderMaster
                        {
                            OrderStatus = "Created",
                            TableNumber = order.TableNumber,
                            WaiterId = userId
                        };

                        _context.Orders.Add(orderMaster);
                        await _context.SaveChangesAsync();

                        foreach (var item in order.OrderDetails)
                        {
                            var menu = await _context.Menus.FindAsync(item.MenuId);
                            var price = menu.Price * item.Quantity;

                            var orderDetail = new OrderDetails
                            {
                                OrderId = orderMaster.OrderId,
                                MenuId = item.MenuId,
                                Quantity = item.Quantity,
                                Price = price
                            };
                            _context.OrderDetails.Add(orderDetail);

                            var recipeItems = await _context.Recipes.Where(r => r.MenuId == item.MenuId).ToListAsync();

                            foreach (var recipeItem in recipeItems)
                            {
                                var inventory = await _context.Inventories.FindAsync(recipeItem.InventoryId);
                                if (inventory != null && inventory.Quantity >= recipeItem.QuantityRequired * item.Quantity)
                                {
                                    inventory.Quantity -= recipeItem.QuantityRequired * item.Quantity;
                                    _context.Inventories.Update(inventory);

                                    var inventoryTransaction = new InventoryTransaction
                                    {
                                        InventoryId = inventory.InventoryId,
                                        TransactionDate = DateTime.Now,
                                        Quantity = -recipeItem.QuantityRequired * item.Quantity,
                                        TransactionType = TransactionType.Subtraction,
                                        Description = $"Order {orderMaster.OrderId} created"
                                    };
                                    _context.InventoryTransactions.Add(inventoryTransaction);
                                }
                                else
                                {
                                    throw new InvalidOperationException($"Insufficient quantity for menu with ID {recipeItem.MenuId}");
                                }
                            }
                        }

                        await _context.SaveChangesAsync();
                        await transaction.CommitAsync();
                        return Ok(orderMaster);
                    }
                    catch (Exception ex)
                    {
                        await transaction.RollbackAsync();
                        return StatusCode(StatusCodes.Status500InternalServerError, $"An error occurred while processing the order: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, $"An error occurred while processing the order: {ex.Message}");
            }
        }


        [HttpPut]
        public async Task<IActionResult> Put([FromBody] OrderModel order)
        {
            using (var transaction = await _context.Database.BeginTransactionAsync())
            {
                try
                {
                    var orderId = order.OrderId;
                    var orderMaster = await _context.Orders.Include(o => o.OrderDetails)
                                                           .FirstOrDefaultAsync(o => o.OrderId == orderId);

                    if (orderMaster == null)
                    {
                        return NotFound($"Order with ID {orderId} not found.");
                    }

                    var updatedMenuIds = order.OrderDetails.Select(od => od.MenuId).ToList();
                    var removedOrderDetails = orderMaster.OrderDetails.Where(od => !updatedMenuIds.Contains((int)od.MenuId)).ToList();

                    foreach (var removedItem in removedOrderDetails)
                    {
                        var recipeItems = await _context.Recipes.Where(r => r.MenuId == removedItem.MenuId).ToListAsync();

                        foreach (var recipeItem in recipeItems)
                        {
                            var inventory = await _context.Inventories.FindAsync(recipeItem.InventoryId);
                            if (inventory != null)
                            {
                                inventory.Quantity += recipeItem.QuantityRequired * removedItem.Quantity;
                                _context.Inventories.Update(inventory);

                                var inventoryTransaction = new InventoryTransaction
                                {
                                    InventoryId = inventory.InventoryId,
                                    TransactionDate = DateTime.Now,
                                    Quantity = recipeItem.QuantityRequired * removedItem.Quantity,
                                    TransactionType = TransactionType.Addition,
                                    Description = $"Order {orderMaster.OrderId} updated - item removed"
                                };
                                _context.InventoryTransactions.Add(inventoryTransaction);
                            }
                        }

                        _context.OrderDetails.Remove(removedItem);
                    }

                    foreach (var item in order.OrderDetails)
                    {
                        var existingOrderDetail = orderMaster.OrderDetails.FirstOrDefault(od => od.MenuId == item.MenuId);

                        if (existingOrderDetail == null)
                        {
                            var menu = await _context.Menus.FindAsync(item.MenuId);
                            var price = menu.Price * item.Quantity;

                            var newOrderDetail = new OrderDetails
                            {
                                OrderId = orderMaster.OrderId,
                                MenuId = item.MenuId,
                                Quantity = item.Quantity,
                                Price = price
                            };
                            _context.OrderDetails.Add(newOrderDetail);

                            var recipeItems = await _context.Recipes.Where(r => r.MenuId == item.MenuId).ToListAsync();
                            foreach (var recipeItem in recipeItems)
                            {
                                var inventory = await _context.Inventories.FindAsync(recipeItem.InventoryId);
                                if (inventory != null && inventory.Quantity >= recipeItem.QuantityRequired * item.Quantity)
                                {
                                    inventory.Quantity -= recipeItem.QuantityRequired * item.Quantity;
                                    _context.Inventories.Update(inventory);

                                    var inventoryTransaction = new InventoryTransaction
                                    {
                                        InventoryId = inventory.InventoryId,
                                        TransactionDate = DateTime.Now,
                                        Quantity = -recipeItem.QuantityRequired * item.Quantity,
                                        TransactionType = TransactionType.Subtraction,
                                        Description = $"Order {orderMaster.OrderId} updated - new item added"
                                    };
                                    _context.InventoryTransactions.Add(inventoryTransaction);
                                }
                                else
                                {
                                    throw new InvalidOperationException($"Insufficient quantity for menu with ID {recipeItem.MenuId}");
                                }
                            }
                        }
                        else
                        {
                            var menu = await _context.Menus.FindAsync(item.MenuId);
                            var price = menu.Price * item.Quantity;

                            var quantityDifference = item.Quantity - existingOrderDetail.Quantity;

                            existingOrderDetail.Quantity = item.Quantity;
                            existingOrderDetail.Price = price;
                            _context.OrderDetails.Update(existingOrderDetail);

                            var recipeItems = await _context.Recipes.Where(r => r.MenuId == item.MenuId).ToListAsync();
                            foreach (var recipeItem in recipeItems)
                            {
                                var inventory = await _context.Inventories.FindAsync(recipeItem.InventoryId);
                                if (inventory != null && inventory.Quantity >= recipeItem.QuantityRequired * quantityDifference)
                                {
                                    inventory.Quantity -= recipeItem.QuantityRequired * quantityDifference;
                                    _context.Inventories.Update(inventory);

                                    var inventoryTransaction = new InventoryTransaction
                                    {
                                        InventoryId = inventory.InventoryId,
                                        TransactionDate = DateTime.Now,
                                        Quantity = -recipeItem.QuantityRequired * quantityDifference,
                                        TransactionType = TransactionType.Subtraction,
                                        Description = $"Order {orderMaster.OrderId} updated - item quantity changed"
                                    };
                                    _context.InventoryTransactions.Add(inventoryTransaction);
                                }
                                else
                                {
                                    throw new InvalidOperationException($"Insufficient quantity for menu with ID {recipeItem.MenuId}");
                                }
                            }
                        }
                    }

                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync();

                    return Ok(orderMaster);
                }
                catch (Exception ex)
                {
                    await transaction.RollbackAsync();
                    return StatusCode(StatusCodes.Status500InternalServerError, $"An error occurred while updating the order: {ex.Message}");
                }
            }
        }

        [HttpPatch("status/{id}")]
        public async Task<IActionResult> PatchOrderStatus(int id, [FromBody] string newStatus)
        {
            try
            {
                using (var transaction = await _context.Database.BeginTransactionAsync())
                {
                    var order = await _context.Orders.Include(o => o.OrderDetails)
                                                     .FirstOrDefaultAsync(o => o.OrderId == id);
                    if (order == null)
                    {
                        return NotFound($"Order with ID {id} not found.");
                    }

                    order.OrderStatus = newStatus;

                    if (newStatus == "Cancelled")
                    {
                        var orderDetails = await _context.OrderDetails
                            .Where(od => od.OrderId == id)
                            .ToListAsync();

                        foreach (var orderDetail in orderDetails)
                        {
                            var recipeItems = await _context.Recipes
                                .Where(r => r.MenuId == orderDetail.MenuId)
                                .ToListAsync();

                            foreach (var recipeItem in recipeItems)
                            {
                                var inventory = await _context.Inventories
                                    .FindAsync(recipeItem.InventoryId);

                                if (inventory != null)
                                {
                                    inventory.Quantity += recipeItem.QuantityRequired * orderDetail.Quantity;
                                    _context.Inventories.Update(inventory);

                                    var inventoryTransaction = new InventoryTransaction
                                    {
                                        InventoryId = inventory.InventoryId,
                                        TransactionDate = DateTime.Now,
                                        Quantity = recipeItem.QuantityRequired * orderDetail.Quantity,
                                        TransactionType = TransactionType.Addition,
                                        Description = $"Order {order.OrderId} cancelled"
                                    };
                                    _context.InventoryTransactions.Add(inventoryTransaction);
                                }
                            }
                        }
                    }
                    else if (newStatus == "completed")
                    {
                        var existingBilling = await _context.Billings.FirstOrDefaultAsync(b => b.OrderId == order.OrderId);

                        if (existingBilling != null)
                        {
                            existingBilling.TotalAmount = order.OrderDetails?.Sum(od => od.Price * od.Quantity) ?? 0;
                            existingBilling.BillingDate = DateTime.Now;
                            existingBilling.Paid = false;

                            _context.Billings.Update(existingBilling);
                        }
                        else
                        {
                            var billingDetails = new Billing
                            {
                                OrderId = order.OrderId,
                                TotalAmount = order.OrderDetails?.Sum(od => od.Price * od.Quantity) ?? 0,
                                BillingDate = DateTime.Now,
                                Paid = false
                            };

                            _context.Billings.Add(billingDetails);
                        }
                    }

                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync();

                    return Ok(order);
                }
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, $"An error occurred: {ex.Message}");
            }
        }
        [HttpGet("report/top-menus")]
        public async Task<ActionResult> GetTopMenusReport(DateTime startDate, DateTime endDate)
        {
            var topMenus = await _context.OrderDetails
                .Where(od => od.Order.OrderDate >= startDate && od.Order.OrderDate <= endDate)
                .GroupBy(od => od.MenuId)
                .Select(g => new
                {
                    MenuId = g.Key,
                    MenuName = g.FirstOrDefault().Menu.MenuName,
                    TotalQuantity = g.Sum(od => od.Quantity)
                })
                .OrderByDescending(g => g.TotalQuantity)
                .Take(5)
                .ToListAsync();

            return Ok(topMenus);
        }

        [HttpGet("report/waiter-performance")]
        public async Task<ActionResult> GetWaiterPerformanceReport(DateTime startDate, DateTime endDate)
        {
            var waiterPerformance = await _context.Orders
                .Where(o => o.OrderDate >= startDate && o.OrderDate <= endDate)
                .GroupBy(o => o.WaiterId)
                .Select(g => new
                {
                    WaiterId = g.Key,
                    WaiterName = g.FirstOrDefault().Waiter.UserName,
                    OrderCount = g.Count()
                })
                .ToListAsync();

            return Ok(waiterPerformance);
        }


        [HttpGet("report/daily-orders")]
        public async Task<ActionResult> GetDailyOrdersReport(DateTime startDate, DateTime endDate)
        {
            var dailyOrders = await _context.Orders
                .Where(o => o.OrderDate >= startDate && o.OrderDate <= endDate)
                .GroupBy(o => o.OrderDate.Date)
                .Select(g => new
                {
                    Date = g.Key,
                    OrderCount = g.Count()
                })
                .ToListAsync();

            return Ok(dailyOrders);
        }
        [HttpGet("report/monthly-revenue")]
        public async Task<ActionResult> GetMonthlyRevenueReport(int year)
        {
            var monthlyRevenue = await _context.Orders
                .Where(o => o.OrderDate.Year == year)
                .GroupBy(o => o.OrderDate.Month)
                .Select(g => new
                {
                    Month = g.Key,
                    TotalRevenue = g.Sum(o => o.OrderDetails.Sum(od => od.Quantity * od.Price))
                })
                .ToListAsync();

            return Ok(monthlyRevenue);
        }


        // GET: OrderController/Delete/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id)
        {
            try
            {
                var order = await _context.Orders.FindAsync(id);
                if (order == null)
                {
                    return NotFound($"Order with ID {id} not found.");
                }

                _context.Orders.Remove(order);
                await _context.SaveChangesAsync();

                return Ok("Order has been deleted successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        
    }
}
