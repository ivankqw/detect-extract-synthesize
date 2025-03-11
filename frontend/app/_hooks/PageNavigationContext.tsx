import { createContext, useContext } from 'react';

export const PageNavigationContext = createContext({
  pageNumber: 1,
  navigateToPage: (page: number) => {},
});

export const usePageNavigation = () => useContext(PageNavigationContext);