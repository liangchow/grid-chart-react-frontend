type Props = {
  onClick: () => void
  disabled?: boolean
  text?: string
}

function Button({ onClick, text }: Props) {

  return (
    <button onClick={onClick} className='px-8 mx-auto py-4 rounded-md border-2 bg-slate-500 border-blue-400 border-solid blueShadow duration-200'>
      <p>{text}</p>
    </button>
  )
}

export default Button
