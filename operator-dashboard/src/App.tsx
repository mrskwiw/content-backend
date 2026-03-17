import { RouterProvider } from 'react-router-dom';
import { router } from '@/router';
import { AppProviders } from '@/providers/AppProviders';
import { Toaster } from 'sonner';

function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} />
      <Toaster position="top-right" richColors closeButton />
    </AppProviders>
  );
}

export default App;
