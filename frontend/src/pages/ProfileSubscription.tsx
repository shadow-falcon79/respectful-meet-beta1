import { useEffect, useState } from "react";
import { Check, Clock3, Crown, Star } from "lucide-react";
import SubPageHeader from "../components/SubPageHeader";
import { createCheckout, getSubscriptionPlans, getSubscriptionStatus, type SubscriptionPlan, type SubscriptionStatus } from "../api/subscription";

const labels: Record<string, { name: string; label?: string; featured?: boolean }> = {
  DAILY: { name: "1 DAY" }, WEEKLY: { name: "7 DAYS", label: "BEST VALUE", featured: true },
  MONTHLY: { name: "30 DAYS", label: "PREMIUM" }, YEARLY: { name: "1 YEAR", label: "BEST VALUE" },
};

export default function ProfileSubscription() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [selected, setSelected] = useState<string>("MONTHLY");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    Promise.all([getSubscriptionPlans(), getSubscriptionStatus()])
      .then(([p, s]) => { setPlans(p); setStatus(s); if (s.plan) setSelected(s.plan); })
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load Premium plans."))
      .finally(() => setLoading(false));
  }, []);

  const selectedPlan = plans.find((p) => p.plan === selected);
  return <section className="page subscription-page"><SubPageHeader title="Premium" backTo="/profile" />
    {loading && <p>Loading Premium plans…</p>}
    {error && <p role="alert">{error}</p>}
    {status && <div className="subscription-hero"><div className="subscription-hero__icon"><Crown size={21}/></div><div><span>Current plan</span><strong>{status.is_premium ? status.plan : "FREE"}</strong></div>{status.is_premium && <small><Clock3 size={13}/> Active until {status.expires_at ? new Date(status.expires_at).toLocaleDateString() : "—"}</small>}</div>}
    <div className="subscription-title"><h2>Unlock more connections</h2><p>Premium status is controlled by the backend. Payments are never simulated in this beta.</p></div>
    <div className="subscription-plans">{plans.map((p) => { const meta: { name: string; label?: string; featured?: boolean } = labels[p.plan] ?? { name: p.plan }; return <button key={p.plan} type="button" className={`subscription-plan ${selected===p.plan?"selected":""} ${meta.featured?"featured":""}`} onClick={() => setSelected(p.plan)}><div className="subscription-plan__top"><div><span className="subscription-plan__name">{meta.name}</span>{meta.label&&<span className="subscription-plan__label">{meta.label}</span>}<small>{p.duration_days} day{p.duration_days===1?"":"s"}</small></div><div className="subscription-plan__price"><strong>{p.stars_price}</strong><span>⭐</span></div></div><ul><li><Check size={14}/> {p.call_minutes_per_day} min/day audio & video</li><li><Check size={14}/> Premium daily limits</li><li><Check size={14}/> Advanced access</li></ul><span className="subscription-radio">{selected===p.plan?"Selected":"Choose"}</span></button>; })}</div>
    {selectedPlan && <div className="subscription-checkout"><div><span>Selected</span><strong>{labels[selectedPlan.plan]?.name ?? selectedPlan.plan} · {selectedPlan.stars_price} ⭐</strong></div><button
        className="btn btn-primary"
        disabled={checkoutLoading}
        onClick={async () => {
          if (!selectedPlan) return;
          setCheckoutLoading(true);
          setError(null);
          try {
            const checkout = await createCheckout(selectedPlan.plan);
            window.location.href = checkout.invoice_url;
          } catch (e) {
            setError(e instanceof Error ? e.message : "Unable to start Telegram Stars checkout.");
          } finally {
            setCheckoutLoading(false);
          }
        }}
      >
        {checkoutLoading ? "Opening secure Telegram checkout…" : "Pay securely with Telegram Stars ⭐"}
      </button>
      <p><Star size={13}/> You will be redirected to Telegram's secure checkout. Premium activates only after Telegram confirms the payment.</p></div>}
  </section>;
}
