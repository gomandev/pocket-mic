'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'

export async function login(formData: FormData) {
    const supabase = await createClient()

    const data = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
    }

    try {
        const { error } = await supabase.auth.signInWithPassword(data)

        if (error) {
            redirect(`/login?error=${encodeURIComponent(error.message)}`)
        }
    } catch (err: any) {
        console.error('Login error:', err)
        redirect(`/login?error=${encodeURIComponent('Authentication service is unavailable. It might be waking up, please try again in a minute.')}`)
    }

    revalidatePath('/', 'layout')
    redirect('/projects')
}

export async function signup(formData: FormData) {
    const supabase = await createClient()

    const data = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
    }

    try {
        const { data: signUpData, error } = await supabase.auth.signUp(data)

        if (error) {
            redirect(`/login?error=${encodeURIComponent(error.message)}`)
        }

        // If email confirmation is required, Supabase returns a user with identities = []
        // when the user already exists, or a valid user that needs to confirm email
        if (signUpData?.user?.identities?.length === 0) {
            redirect('/login?error=' + encodeURIComponent('An account with this email already exists.'))
        }

        // Check if email confirmation is needed
        if (signUpData?.user && !signUpData?.session) {
            redirect('/login?error=' + encodeURIComponent('Check your email for a confirmation link to complete signup.'))
        }
    } catch (err: any) {
        console.error('Signup error:', err)
        // Check if the error is a redirect error, which we should NOT catch
        if (err?.message === 'NEXT_REDIRECT') throw err;

        redirect(`/login?error=${encodeURIComponent('Database is waking up from sleep. Please try again in about 60 seconds.')}`)
    }

    revalidatePath('/', 'layout')
    redirect('/projects')
}

export async function logout() {
    const supabase = await createClient()
    await supabase.auth.signOut()
    revalidatePath('/', 'layout')
    redirect('/login')
}
