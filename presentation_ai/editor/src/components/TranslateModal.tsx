import { useState } from 'react'
import { SUPPORTED_LANGUAGES } from '../constants/languages'

const BACKEND_URL = `http://${window.location.hostname}:8000`;

interface TranslateModalProps {
  isOpen: boolean
  onClose: () => void
  deck: any
  onTranslated: (translatedDeck: any) => void
}

const TranslateModal = ({ 
  isOpen, onClose, deck, onTranslated 
}: TranslateModalProps) => {
  const [selectedLang, setSelectedLang] = useState('hi')
  const [isTranslating, setIsTranslating] = useState(false)
  const [progress, setProgress] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredLanguages = SUPPORTED_LANGUAGES.filter(lang =>
    lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lang.native.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleTranslate = async () => {
    const targetLang = SUPPORTED_LANGUAGES.find(
      l => l.code === selectedLang
    )
    if (!targetLang) return

    setIsTranslating(true)
    setProgress('Translating your presentation...')

    try {
      const response = await fetch(`${BACKEND_URL}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deck_data: deck,
          target_language: targetLang.code,
          target_language_name: targetLang.name
        })
      })

      if (!response.ok) {
        throw new Error('Translation request failed')
      }

      const data = await response.json()
      setProgress('Translation complete!')
      
      setTimeout(() => {
        onTranslated(data.translated_deck)
        onClose()
        setIsTranslating(false)
        setProgress('')
      }, 800)

    } catch (error) {
      setProgress('Translation failed. Please try again.')
      setIsTranslating(false)
    }
  }

  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: '#fff',
        borderRadius: '16px',
        padding: '28px',
        width: '420px',
        maxHeight: '80vh',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <div>
            <h2 style={{
              fontSize: '20px', fontWeight: '700',
              color: '#1A1A2E', margin: 0
            }}>
              🌐 Translate Presentation
            </h2>
            <p style={{
              fontSize: '13px', color: '#666',
              margin: '4px 0 0'
            }}>
              Translate all slides using AI
            </p>
          </div>
          <button onClick={onClose} style={{
            border: 'none', background: 'none',
            fontSize: '20px', cursor: 'pointer', color: '#666'
          }}>✕</button>
        </div>

        {/* Search languages */}
        <input
          type="text"
          placeholder="🔍 Search language..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{
            padding: '10px 14px',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            fontSize: '14px',
            marginBottom: '12px',
            outline: 'none'
          }}
        />

        {/* Language list */}
        <div style={{
          overflowY: 'auto',
          flex: 1,
          border: '1px solid #E5E7EB',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          {filteredLanguages.map((lang) => (
            <div
              key={lang.code}
              onClick={() => setSelectedLang(lang.code)}
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: selectedLang === lang.code 
                  ? '#EEF2FF' : 'white',
                borderBottom: '1px solid #F3F4F6'
              }}
            >
              <div>
                <div style={{
                  fontWeight: selectedLang === lang.code 
                    ? '600' : '400',
                  color: '#1A1A2E',
                  fontSize: '14px'
                }}>
                  {lang.name}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: '#666'
                }}>
                  {lang.native}
                </div>
              </div>
              {selectedLang === lang.code && (
                <span style={{ color: '#6366F1' }}>✓</span>
              )}
            </div>
          ))}
        </div>

        {/* Progress message */}
        {progress && (
          <div style={{
            textAlign: 'center',
            fontSize: '13px',
            color: '#6366F1',
            marginBottom: '12px',
            padding: '8px',
            background: '#EEF2FF',
            borderRadius: '8px'
          }}>
            {isTranslating && '⏳ '}{progress}
          </div>
        )}

        {/* Buttons */}
        <div style={{
          display: 'flex',
          gap: '10px'
        }}>
          <button
            onClick={onClose}
            disabled={isTranslating}
            style={{
              flex: 1, padding: '12px',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
              background: 'white',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleTranslate}
            disabled={isTranslating}
            style={{
              flex: 1, padding: '12px',
              border: 'none',
              borderRadius: '8px',
              background: isTranslating 
                ? '#A5B4FC' : '#6366F1',
              color: 'white',
              cursor: isTranslating 
                ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            {isTranslating ? '⏳ Translating...' : '🌐 Translate'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default TranslateModal
