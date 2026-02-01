'use client';

import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/lib/store/store';
import { setCredentials, logout } from '@/lib/store/features/auth/authSlice';
import { Button } from '@/components/ui/button';

export default function ReduxTest() {
  const dispatch = useDispatch();
  // READ from the store
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  const handleForceLogin = () => {
    // WRITE to the store
    dispatch(setCredentials({
      user: {
        id: '999',
        name: 'Test Agent',
        email: 'agent@cleardrive.lk',
        role: 'admin'
      },
      token: 'fake-jwt-token'
    }));
  };

  return (
    <div className="fixed bottom-4 right-4 p-4 bg-gray-900 border border-gray-700 rounded-lg text-white text-xs font-mono z-50 shadow-xl">
      <h3 className="text-[#FE7743] font-bold mb-2">🔴 REDUX STATE MONITOR</h3>
      
      <div className="mb-4 space-y-1">
        <p>Status: <span className={isAuthenticated ? "text-green-500" : "text-red-500"}>
          {isAuthenticated ? "LOGGED IN" : "LOGGED OUT"}
        </span></p>
        
        {user && <p>User: {user.name}</p>}
      </div>

      <div className="flex gap-2">
        <Button 
          onClick={handleForceLogin}
          className="h-6 text-xs bg-green-600 hover:bg-green-700"
        >
          Force Login
        </Button>
        
        <Button 
          onClick={() => dispatch(logout())}
          className="h-6 text-xs bg-red-600 hover:bg-red-700"
        >
          Force Logout
        </Button>
      </div>
    </div>
  );
}