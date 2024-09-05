using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Orders;
using RMS_API.Data.Users;
using RMS_API.Models.Orders;
using RMS_API.Models.Users;
using StackExchange.Redis;

namespace RMS_API.Controllers.Orders
{
    [Route("api/[controller]")]
    [ApiController]
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
                         WaiterId = ur.WaiterId
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
            var orderDetails =_context.OrderDetails.Where(od => od.OrderId == id).ToList();

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
        // POST: OrderController/Post
        public async Task<IActionResult> Post([FromBody] OrderModel order)
        {
            try
            {
                using (var transaction = await _context.Database.BeginTransactionAsync())
                {
                    try
                    {
                        var orderMaster = new OrderMaster
                        {
                            OrderStatus = order.OrderStatus,
                            TableNumber = order.TableNumber,
                            WaiterId = order.WaiterId
                        };

                        _context.Orders.Add(orderMaster);
                        await _context.SaveChangesAsync();

                        foreach (var item in order.OrderDetails)
                        {
                            var orderDetail = new OrderDetails
                            {
                                OrderId = orderMaster.OrderId,
                                MenuId = item.MenuId,
                                Quantity = item.Quantity,
                                Price = item.Price
                            };
                            _context.OrderDetails.Add(orderDetail);
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
                // Log the exception
                return StatusCode(StatusCodes.Status500InternalServerError, $"An error occurred while processing the order: {ex.Message}");
            }
        }

        [HttpPut]
        // Put: OrderController/Edit/5
        public ActionResult Edit(int id)
        {
            return View();
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
