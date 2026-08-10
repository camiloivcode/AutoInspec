import { useQuery } from '@tanstack/react-query'

export function useSystemStatus() {
  const { data, isError } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error('health check failed')
      return res.json()
    },
    refetchInterval: 30000,
    retry: 1,
  })

  return { online: !isError && !!data }
}
