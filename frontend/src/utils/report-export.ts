export async function exportElementReport(
  element: HTMLElement | null,
  format: 'png' | 'pdf',
  name = 'FusionReport',
  options: { signatureLine?: boolean } = {},
) {
  if (!element) {
    throw new Error('报告内容尚未渲染，无法导出')
  }

  const html2canvas = (await import('html2canvas')).default
  const canvas = await html2canvas(element, { backgroundColor: null, scale: 2 })
  const fileName = `${name}-${new Date().toISOString()}`

  if (format === 'png') {
    const link = document.createElement('a')
    link.download = `${fileName}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    return
  }

  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF('p', 'mm', 'a4')
  const pdfWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  const pdfHeight = (canvas.height * pdfWidth) / canvas.width
  pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, pdfWidth, pdfHeight)
  if (options.signatureLine) {
    pdf.setDrawColor(150)
    pdf.line(20, pageHeight - 37, 80, pageHeight - 37)
    pdf.setFontSize(10)
    pdf.text('管理员签字', 20, pageHeight - 27)
  }
  pdf.save(`${fileName}.pdf`)
}
