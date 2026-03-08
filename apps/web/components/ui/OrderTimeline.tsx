// apps/web/components/OrderTimeline.tsx

import { useEffect, useState } from 'react';

interface TimelineEvent {
  id: string;
  from_status: string | null;
  to_status: string;
  notes: string | null;
  changed_by_name: string;
  changed_by_email: string;
  created_at: string;
}

interface OrderTimelineProps {
  orderId: string;
}

export function OrderTimeline({ orderId }: OrderTimelineProps) {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTimeline();
  }, [orderId]);

  const fetchTimeline = async () => {
    try {
      const response = await fetch(`/api/v1/orders/${orderId}/timeline`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch timeline');
      }

      const data = await response.json();
      setTimeline(data.timeline);
      setLoading(false);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, string> = {
      'CREATED': '📝',
      'PAYMENT_CONFIRMED': '💳',
      'ASSIGNED_TO_EXPORTER': '👤',
      'SHIPPING_STARTED': '🚢',
      'IN_TRANSIT': '🌊',
      'CUSTOMS_CLEARANCE': '🛃',
      'DELIVERED': '✅',
      'CANCELLED': '❌'
    };
    return icons[status] || '📌';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'CREATED': 'bg-blue-100 text-blue-800',
      'PAYMENT_CONFIRMED': 'bg-green-100 text-green-800',
      'ASSIGNED_TO_EXPORTER': 'bg-purple-100 text-purple-800',
      'SHIPPING_STARTED': 'bg-indigo-100 text-indigo-800',
      'IN_TRANSIT': 'bg-cyan-100 text-cyan-800',
      'CUSTOMS_CLEARANCE': 'bg-yellow-100 text-yellow-800',
      'DELIVERED': 'bg-green-200 text-green-900',
      'CANCELLED': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        {error}
      </div>
    );
  }

  return (
    <div className="order-timeline">
      <h3 className="text-xl font-semibold mb-4">Order Timeline</h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

        {/* Timeline events */}
        <div className="space-y-6">
          {timeline.map((event, index) => (
            <div key={event.id} className="relative pl-10">
              {/* Icon */}
              <div className="absolute left-0 w-8 h-8 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center text-lg">
                {getStatusIcon(event.to_status)}
              </div>

              {/* Content */}
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(event.to_status)}`}>
                      {event.to_status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {formatDate(event.created_at)}
                  </span>
                </div>

                {event.notes && (
                  <p className="text-gray-700 mb-2">
                    {event.notes}
                  </p>
                )}

                <p className="text-sm text-gray-500">
                  Changed by: <span className="font-medium">{event.changed_by_name}</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {timeline.length === 0 && (
        <p className="text-center text-gray-500 py-8">
          No timeline events yet
        </p>
      )}
    </div>
  );
}
