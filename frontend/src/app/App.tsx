import { QueryProvider } from './providers/QueryProvider';
import { MeasurePage } from '@pages/measure/MeasurePage';

export function App() {
  return (
    <QueryProvider>
      <MeasurePage />
    </QueryProvider>
  );
}
