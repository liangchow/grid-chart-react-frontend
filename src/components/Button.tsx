type Props = {
  onClick: () => void
  disabled?: boolean
  text?: string
}

function Button({ onClick, text }: Props) {

  return (
    <button onClick={onClick} className='mx-auto rounded-full overflow-hidden duration-200 border-2 border-solid border-indigo-600 hover:opacity-60'>
      <p className="px-4 sm:px-10 py-2 sm:py-3 rounded-full whitespace-nowrap bg-white cursor-pointer ">{text}</p>
    </button>
  )
}

export default Button
