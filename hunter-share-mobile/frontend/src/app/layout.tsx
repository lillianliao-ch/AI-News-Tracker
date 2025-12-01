import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '猎头协作 - 专业人才网络',
  description: '猎头信息分享与协作平台，连接优秀人才与企业机会',
  keywords: '猎头,人才推荐,职位分享,求职,招聘',
  authors: [{ name: '猎头协作平台' }],
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    url: 'https://hunter-share.com',
    title: '猎头协作 - 专业人才网络',
    description: '猎头信息分享与协作平台，连接优秀人才与企业机会',
    siteName: '猎头协作',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: '猎头协作平台',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: '猎头协作 - 专业人才网络',
    description: '猎头信息分享与协作平台，连接优秀人才与企业机会',
    images: ['/og-image.png'],
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}

