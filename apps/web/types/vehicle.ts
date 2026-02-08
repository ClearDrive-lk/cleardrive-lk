export interface Vehicle {
    id: string;
    year: number;
    make: string;
    model: string;
    trim: string;
    chassisCode: string; // e.g., "CBA-ZE2"
    mileage: number; // in km
    engineCC: number;
    fuel: 'Petrol' | 'Hybrid' | 'Diesel' | 'Electric';
    transmission: 'AT' | 'MT' | 'CVT';
    color: string;
    
    // Auction Data
    auctionHouse: 'USS Tokyo' | 'JAA' | 'CAI' | 'Honda';
    lotNumber: string;
    grade: string; // e.g., "4.5", "S", "R"
    inspectionScore: {
      exterior: string;
      interior: string;
    };
    
    // Pricing
    priceJPY: number; // Start/Current Bid
    estimatedLandedCostLKR: number; // The "AI Calculated" price
    
    // Media
    imageUrl: string;
    
    // Status
    status: 'Live' | 'Sold' | 'Upcoming';
    endTime: string; // ISO String
  }