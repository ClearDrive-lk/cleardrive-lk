const PAYHERE_CHECKOUT_URL = "https://sandbox.payhere.lk/pay/checkout";

export interface PayHereOrderData {
  merchantId: string;
  returnUrl: string;
  cancelUrl: string;
  notifyUrl: string;
  orderId: string;
  items: string;
  amount: number | string;
  customer: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    country: string;
  };
}

const escapeHtml = (value: string) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

const PAYHERE_FIELD_KEYS = [
  "merchant_id",
  "return_url",
  "cancel_url",
  "notify_url",
  "order_id",
  "items",
  "currency",
  "amount",
  "first_name",
  "last_name",
  "email",
  "phone",
  "address",
  "city",
  "country",
  "hash",
] as const;

export function generatePayHereForm(orderData: PayHereOrderData, hash: string) {
  const fields: Record<string, string> = {
    merchant_id: orderData.merchantId,
    return_url: orderData.returnUrl,
    cancel_url: orderData.cancelUrl,
    notify_url: orderData.notifyUrl,
    order_id: orderData.orderId,
    items: orderData.items,
    currency: "LKR",
    amount: Number(orderData.amount).toFixed(2),
    first_name: orderData.customer.firstName,
    last_name: orderData.customer.lastName,
    email: orderData.customer.email,
    phone: orderData.customer.phone,
    address: orderData.customer.address,
    city: orderData.customer.city,
    country: orderData.customer.country,
    hash,
  };

  const inputs = Object.entries(fields)
    .map(
      ([name, value]) =>
        `<input type="hidden" name="${escapeHtml(name)}" value="${escapeHtml(value)}" />`,
    )
    .join("");

  return `<form id="payhere-checkout-form" method="POST" action="${PAYHERE_CHECKOUT_URL}" style="display:none">${inputs}</form>`;
}

export function submitPayHereForm(
  orderData: PayHereOrderData,
  hash: string,
  actionUrl?: string,
) {
  const markup = generatePayHereForm(orderData, hash);
  const container = document.createElement("div");
  container.innerHTML = markup;

  const form = container.querySelector<HTMLFormElement>("#payhere-checkout-form");
  if (!form) {
    throw new Error("Failed to generate PayHere form");
  }

  if (actionUrl) {
    form.action = actionUrl;
  }

  document.body.appendChild(form);
  form.submit();
}

export function buildPayHereOrderDataFromParams(
  params: Record<string, string>,
): {
  orderData: PayHereOrderData;
  hash: string;
} {
  const sanitizedParams = PAYHERE_FIELD_KEYS.reduce<Record<string, string>>(
    (accumulator, key) => {
      accumulator[key] = params[key] ?? "";
      return accumulator;
    },
    {},
  );

  const orderData: PayHereOrderData = {
    merchantId: sanitizedParams.merchant_id,
    returnUrl: sanitizedParams.return_url,
    cancelUrl: sanitizedParams.cancel_url,
    notifyUrl: sanitizedParams.notify_url,
    orderId: sanitizedParams.order_id,
    items: sanitizedParams.items,
    amount: sanitizedParams.amount,
    customer: {
      firstName: sanitizedParams.first_name,
      lastName: sanitizedParams.last_name,
      email: sanitizedParams.email,
      phone: sanitizedParams.phone,
      address: sanitizedParams.address,
      city: sanitizedParams.city,
      country: sanitizedParams.country,
    },
  };

  return {
    orderData,
    hash: sanitizedParams.hash,
  };
}
