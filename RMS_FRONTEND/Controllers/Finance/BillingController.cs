using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Models.Finance;
using RMS_FRONTEND.Models.Orders;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Finance
{
    public class BillingController : Controller
    {
        private readonly IApiCall _apiCall;

        public BillingController(IApiCall apiCall)
        {
            _apiCall = apiCall;
        }

        // GET: Billing
        public async Task<IActionResult> Index()
        {
			var responseData = await _apiCall.GetAsync("Billing");
			var billings = JsonConvert.DeserializeObject<IEnumerable<BillingModel>>(responseData);
            return View(billings);
		}

        // GET: Billing/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var responseData = await _apiCall.GetAsync("Billing/",$"{id}");
            var billings = JsonConvert.DeserializeObject<BillingModel>(responseData);
            return View(billings);
        }

        // GET: Billing/Create
        public async Task<IActionResult> Create()
        {
            var responseData = await _apiCall.GetAsync("Order");
            var orders = JsonConvert.DeserializeObject<IEnumerable<OrderModel>>(responseData);
            ViewData["OrderId"] = new SelectList(orders, "OrderId", "OrderId");
            return View();
        }

        // POST: Billing/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("OrderId,TotalAmount,BillingDate,Paid")] BillingModel billing)
        {
            if (ModelState.IsValid)
            {
                var responseData = await _apiCall.PostAsync("Billing",billing);
                var orders = JsonConvert.DeserializeObject<IEnumerable<OrderModel>>(responseData);
                return RedirectToAction(nameof(Index));
            }
            return View(billing);
        }

        // GET: Billing/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var orderData = await _apiCall.GetAsync("Order");
            var orders = JsonConvert.DeserializeObject<IEnumerable<OrderModel>>(orderData);
            ViewData["OrderId"] = new SelectList(orders, "OrderId", "OrderId");

            var responseData = await _apiCall.GetAsync("Billing/",$"{id}");
            var billingModel = JsonConvert.DeserializeObject<BillingModel>(responseData);
            return View();
        }

        // POST: Billing/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("BillingId,OrderId,TotalAmount,BillingDate,Paid")] BillingModel billing)
        {
            if (id != billing.BillingId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                var responseData = await _apiCall.PostAsync("Billing",billing);
                var orders = JsonConvert.DeserializeObject<OrderModel>(responseData);
                return RedirectToAction(nameof(Index));
            }
            return View(billing);
        }

        // GET: Billing/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var responseData = await _apiCall.DeleteAsync("Billing/",$"{id}");
            var billing = JsonConvert.DeserializeObject<BillingModel>(responseData);
            return RedirectToAction(nameof(Index));
        }

    }
}
