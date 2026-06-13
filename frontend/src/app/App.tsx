import { QueryProvider } from './providers/QueryProvider';
import { FavMeasurePage } from '@pages/fav/FavMeasurePage';

export function App() {
  return (
    <QueryProvider>
      <FavMeasurePage />
    </QueryProvider>
  );
}
