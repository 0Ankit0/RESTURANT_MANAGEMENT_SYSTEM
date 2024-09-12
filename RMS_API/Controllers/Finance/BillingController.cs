﻿using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Finance;
using RMS_API.Data.Orders;
using RMS_API.Models.Finance;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace RMS_API.Controllers.Finance
{
    [Route("api/[controller]")]
    [ApiController]
    public class BillingController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public BillingController(ApplicationDbContext context)
        {
            _context = context;
        }
        // GET: api/<BillingController>
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Billing>>> Get()
        {
            try
            {
                var billing = await _context.Billings.Where(b=>b.Paid==false).ToListAsync();
                return Ok(billing);

            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");

            }
        }

        // GET api/<BillingController>/5
        [HttpGet("{id}")]
        public async Task<IActionResult> Get(int id)
        {
            try
            {
                // Fetch the Billing record
                var billing = await _context.Billings
                    .Include(b => b.Order) // Include the related Order
                    .ThenInclude(o => o.OrderDetails) // Include the OrderDetails of the Order
                    .ThenInclude(od => od.Menu) // Include the Menu details for each OrderDetail
                    .FirstOrDefaultAsync(b => b.BillingId == id);

                if (billing == null)
                {
                    return NotFound($"Billing with ID {id} not found.");
                }

                // Fetch the order details related to the billing's OrderId
                var orderDetails = billing.Order?.OrderDetails
                    .Select(od => new
                    {
                        od.Menu.MenuName,
                        od.Quantity,
                        od.Price,
                        TotalPrice = od.Quantity * od.Price
                    })
                    .ToList();

                if (orderDetails == null || orderDetails.Count == 0)
                {
                    return NotFound($"No order details found for the Billing with ID {id}.");
                }

                return Ok(new
                {
                    billing.OrderId,
                    billing.TotalAmount,
                    billing.Paid,
                    billing.BillingDate,
                    OrderDetails = orderDetails
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");

            }
        }

        //for partial order
        [HttpPost]
        public async Task<ActionResult> Post([FromBody] BillingModel partialBill)
        {
            try
            {
                // Check if the original order exists
                var originalOrder = await _context.Orders
                    .Include(o => o.OrderDetails)
                    .FirstOrDefaultAsync(o => o.OrderId == partialBill.OrderId);

                if (originalOrder == null)
                {
                    return NotFound($"Order with ID {partialBill.OrderId} not found.");
                }

                // Create a new partial order
                OrderMaster newPartialOrder = new OrderMaster
                {
                    TableNumber = originalOrder.TableNumber,
                    WaiterId = originalOrder.WaiterId,
                    OrderStatus = "Partial",
                    OrderDate = DateTime.Now,
                    UpdatedAt = DateTime.Now,
                    OrderDetails = new List<OrderDetails>()
                };

                decimal billingAmount = 0;

                // Process each item in the partial bill's OrderDetails
                foreach (var orderDetailModel in partialBill.OrderDetails)
                {
                    var originalOrderDetail = originalOrder.OrderDetails
                        .FirstOrDefault(od => od.OrderDetailId == orderDetailModel.OrderDetailId);

                    if (originalOrderDetail == null)
                    {
                        return BadRequest($"OrderDetail with ID {orderDetailModel.OrderDetailId} not found.");
                    }

                    // Ensure the quantity being billed doesn't exceed the original quantity
                    if (orderDetailModel.Quantity > originalOrderDetail.Quantity)
                    {
                        return BadRequest($"Invalid quantity for OrderDetail ID {orderDetailModel.OrderDetailId}. Maximum allowed is {originalOrderDetail.Quantity}.");
                    }

                    // Calculate the total amount for the partial bill item
                    billingAmount += orderDetailModel.Quantity * orderDetailModel.Price;

                    // Create a new OrderDetails item for the partial order
                    var partialOrderDetail = new OrderDetails
                    {
                        MenuId = originalOrderDetail.MenuId,
                        Quantity = orderDetailModel.Quantity,
                        Price = originalOrderDetail.Price
                    };

                    // Add to the new partial order's OrderDetails collection
                    newPartialOrder.OrderDetails.Add(partialOrderDetail);

                    // Update the quantity in the original order's detail if partially billed
                    if (orderDetailModel.Quantity == originalOrderDetail.Quantity)
                    {
                        // Remove the original detail if the entire quantity is moved
                        _context.OrderDetails.Remove(originalOrderDetail);
                    }
                    else
                    {
                        // Reduce the quantity in the original order if only part is billed
                        originalOrderDetail.Quantity -= orderDetailModel.Quantity;
                        _context.OrderDetails.Update(originalOrderDetail);
                    }
                }

                // Add the new partial order to the context
                _context.Orders.Add(newPartialOrder);
                await _context.SaveChangesAsync(); // Save new order to get OrderId

                // Create a new Billing object with the new order's OrderId
                Billing billing = new Billing
                {
                    OrderId = newPartialOrder.OrderId, // Use the new order's ID
                    TotalAmount = billingAmount,
                    BillingDate = DateTime.Now,
                    Paid = false
                };

                // Add the Billing object to the context
                _context.Billings.Add(billing);

                // Save the changes to the database
                await _context.SaveChangesAsync();

                return Ok($"Partial billing of {billingAmount} for Order ID {partialBill.OrderId} created successfully with Billing ID {billing.BillingId} and new Partial Order ID {newPartialOrder.OrderId}.");
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }


        // PATCH api/<BillingController>/5
        [HttpPatch("{id}")]
        public async Task<ActionResult<Billing>> Patch(int id)
        {
            try
            {
                var billing = await _context.Billings.FindAsync(id);

                if (billing == null)
                {
                    return NotFound($"Billing with ID {id} not found.");
                }

                billing.Paid = true;
                _context.Billings.Update(billing);

                await _context.SaveChangesAsync();

                return Ok(billing);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }


        // DELETE api/<BillingController>/5
        [HttpDelete("{id}")]
        public void Delete(int id)
        {
        }
    }
}