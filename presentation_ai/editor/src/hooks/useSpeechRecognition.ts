import { useState, useEffect, useRef } from 'react'

interface UseSpeechRecognitionReturn {
  transcript: string
  isListening: boolean
  startListening: () => void
  stopListening: () => void
  isSupported: boolean
  error: string | null
  resetTranscript: () => void
}

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const [transcript, setTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<any>(null)

  // Check browser support
  const isSupported = typeof window !== 'undefined' && 
    ('SpeechRecognition' in window || 
     'webkitSpeechRecognition' in window)

  const startListening = () => {
    if (!isSupported) return
    setError(null)
    setTranscript('')

    try {
      if (!recognitionRef.current) {
        const SpeechRecognition = 
          (window as any).SpeechRecognition || 
          (window as any).webkitSpeechRecognition
        
        const recognition = new SpeechRecognition()
        recognition.continuous = false      // stop after one sentence
        recognition.interimResults = true   // show words as spoken
        recognition.lang = 'en-US'         // default language

        recognition.onstart = () => {
          setIsListening(true)
          setError(null)
        }

        recognition.onresult = (event: any) => {
          let finalTranscript = ''
          let interimTranscript = ''
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const tr = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              finalTranscript += tr
            } else {
              interimTranscript += tr
            }
          }
          
          setTranscript(finalTranscript || interimTranscript)
        }

        recognition.onerror = (event: any) => {
          setError(`Speech error: ${event.error}`)
          setIsListening(false)
        }

        recognition.onend = () => {
          setIsListening(false)
        }

        recognitionRef.current = recognition
      }

      recognitionRef.current.start()
    } catch (err: any) {
      setError(`Speech recognition start failed: ${err.message}`)
      setIsListening(false)
    }
  }

  const stopListening = () => {
    try {
      recognitionRef.current?.stop()
    } catch (err: any) {
      console.warn("Failed to stop recognition:", err)
    }
    setIsListening(false)
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      try {
        recognitionRef.current?.abort()
      } catch (e) {}
    }
  }, [])

  const resetTranscript = () => {
    setTranscript('')
  }

  return { 
    transcript, isListening, 
    startListening, stopListening, 
    isSupported, error, resetTranscript
  }
}
