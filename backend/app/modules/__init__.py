"""Application modules.

Importing this package is used as a side-effect to ensure SQLAlchemy models are
registered before metadata operations (e.g., migrations, tests).
"""

# Import each module's models to register them with SQLAlchemy's metadata.
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.gdpr import models as _gdpr_models  # noqa: F401
from app.modules.kyc import models as _kyc_models  # noqa: F401
from app.modules.orders import models as _orders_models  # noqa: F401
from app.modules.payments import models as _payments_models  # noqa: F401
from app.modules.security import models as _security_models  # noqa: F401
from app.modules.shipping import models as _shipping_models  # noqa: F401
from app.modules.vehicles import models as _vehicles_models  # noqa: F401
