import { redirect } from 'next/navigation'

export default function Home() {
  // TODO: Story 3.2 - Check auth status and redirect accordingly
  // For now, redirect to login page
  redirect('/login')
}
